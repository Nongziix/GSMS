from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.dbf_engine import DBFSyncEngine
from app import db
from app.models import Brand, CarModel, CarVariant, Color, Car
from sqlalchemy import text
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Dashboard view showing summary statistics."""
    try:
        # Count total stock from stockxp4
        result = db.session.execute(text("SELECT COUNT(*) FROM stockxp4")).fetchone()
        total_stock = result[0] if result else 0
    except Exception:
        total_stock = 0
        
    return render_template('index.html', title="แดชบอร์ด", active_page='dashboard', total_stock=total_stock)

@main_bp.route('/stock')
def stock():
    """Stock table view for vehicle inventory."""
    try:
        # Fetch all records from stockxp4
        query = text("SELECT STKCOD, STKDES, STKGRP, QUANO FROM stockxp4 ORDER BY STKCOD")
        stocks = db.session.execute(query).fetchall()
    except Exception as e:
        stocks = []
        flash(f"ไม่สามารถดึงข้อมูลสต็อกได้: {str(e)}", "danger")
        
    return render_template('stock.html', title="รายการรถในสต็อก", active_page='stock', stocks=stocks)

@main_bp.route('/stockcard/<stkcod>')
def stockcard(stkcod):
    """Detailed stock card for a specific vehicle model/item."""
    try:
        # Fetch product info
        info_query = text("SELECT STKCOD, STKDES FROM stockxp4 WHERE STKCOD = :stkcod")
        product = db.session.execute(info_query, {"stkcod": stkcod}).fetchone()
        
        # Fetch movement from stockcardxp4
        card_query = text("SELECT DOCDAT, RECTYP, DOCNUM, DEPCOD, QUANO, UNITPR, TRNVAL FROM stockcardxp4 WHERE STKCOD = :stkcod ORDER BY DOCDAT, DOCNUM")
        movements = db.session.execute(card_query, {"stkcod": stkcod}).fetchall()
    except Exception as e:
        product = None
        movements = []
        flash(f"ไม่สามารถดึงข้อมูล Stock Card ได้: {str(e)}", "danger")
        
    return render_template('stockcard.html', title=f"Stock Card: {stkcod}", active_page='stock', product=product, movements=movements)

@main_bp.route('/purchase/receive-car', methods=['GET', 'POST'])
def receive_car():
    """Form to receive new car into stock and save to SQLite."""
    if request.method == 'POST':
        try:
            # Create a new Car entry from form data
            new_car = Car(
                vin_no=request.form['vin_no'].strip().upper(),
                engine_no=request.form['engine_no'].strip().upper(),
                variant_id=int(request.form['variant_id']),
                color_ext_id=int(request.form['color_ext_id']) if request.form['color_ext_id'] else None,
                color_int_id=int(request.form['color_int_id']) if request.form['color_int_id'] else None,
                mileage_import=int(request.form['mileage_import'] or 0),
                receive_date=datetime.strptime(request.form['receive_date'], '%Y-%m-%d') if request.form['receive_date'] else datetime.utcnow(),
                express_doc_no=request.form['express_doc_no'],
                express_stkcod=request.form['express_stkcod'],
                cost_before_vat=float(request.form['cost_before_vat'] or 0),
                vat_amount=float(request.form['vat_amount'] or 0),
                net_amount=float(request.form['net_amount'] or 0),
                status='In Stock'
            )
            db.session.add(new_car)
            db.session.commit()
            flash(f"✅ บันทึกรับรถ VIN {new_car.vin_no} เข้าสต็อกเรียบร้อยแล้ว", "success")
            return redirect(url_for('main.stock'))
        except Exception as e:
            db.session.rollback()
            flash(f"❌ บันทึกข้อมูลล้มเหลว: {str(e)}", "danger")

    # Master data for form dropdowns
    brands = Brand.query.order_by(Brand.brand_name).all()
    colors_ext = Color.query.filter_by(color_type='Exterior').order_by(Color.color_name).all()
    colors_int = Color.query.filter_by(color_type='Interior').order_by(Color.color_name).all()
    
    return render_template('purchase_receive.html', 
                           title="รับรถเข้าสต็อก", 
                           active_page='purchase',
                           brands=brands,
                           colors_ext=colors_ext,
                           colors_int=colors_int,
                           now_date=datetime.now().strftime('%Y-%m-%d'))

# API Routes for Dynamic Dropdowns
@main_bp.route('/api/models/<int:brand_id>')
def get_models(brand_id):
    models = CarModel.query.filter_by(brand_id=brand_id).all()
    return jsonify([{'id': m.model_id, 'name': m.model_name} for m in models])

@main_bp.route('/api/variants/<int:model_id>')
def get_variants(model_id):
    variants = CarVariant.query.filter_by(model_id=model_id).all()
    return jsonify([{'id': v.variant_id, 'name': v.variant_name} for v in variants])

@main_bp.route('/api/express-bill/<docnum>')
def get_express_bill(docnum):
    """Fetch bill details from master_aptrn table synced from Express."""
    try:
        # Query from master_aptrn table
        query = text("SELECT DOCNUM, SUPCOD, AMOUNT, VATAMT, NETAMT FROM master_aptrn WHERE DOCNUM = :docnum")
        bill = db.session.execute(query, {"docnum": docnum.strip().upper()}).fetchone()
        
        if bill:
            return jsonify({
                'success': True,
                'docnum': bill.DOCNUM,
                'supcod': bill.SUPCOD,
                'amount': bill.AMOUNT,
                'vatamt': bill.VATAMT,
                'netamt': bill.NETAMT
            })
        return jsonify({'success': False, 'message': 'ไม่พบเลขที่เอกสารนี้ในข้อมูลที่ซิงค์จาก Express'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/api/express-bills')
def get_express_bills():
    """Fetch refined list of car purchase bills using 3-way join logic from Express."""
    try:
        # Join stockcardxp4 + stockxp4 + master_aptrn to find car purchases
        # Filter by STKGRP (รย, ทส) and DOCNUM prefixes
        query = text("""
            SELECT DISTINCT 
                a.DOCNUM, a.DOCDAT, a.YOUREF, s.STKDES, s.STKCOD, 
                a.AMOUNT, a.VATAMT, a.NETAMT, sup.PRENAM || sup.SUPNAM as SUPNAME, a.SUPCOD
            FROM stockcardxp4 c
            JOIN stockxp4 s ON c.STKCOD = s.STKCOD
            JOIN master_aptrn a ON c.DOCNUM = a.DOCNUM
            LEFT JOIN master_supplier sup ON a.SUPCOD = sup.SUPCOD
            WHERE (s.STKGRP IN ('รย', 'ทส', 'เธฃเธข', 'เธ—เธช'))
              AND (a.DOCNUM LIKE 'RR%' OR a.DOCNUM LIKE 'RS%' OR a.DOCNUM LIKE 'RK%')
            ORDER BY a.DOCDAT DESC
        """)
        bills = db.session.execute(query).fetchall()
        
        return jsonify({
            'success': True,
            'data': [
                {
                    'docnum': b.DOCNUM,
                    'docdat': b.DOCDAT,
                    'youref': b.YOUREF,
                    'stkdes': b.STKDES,
                    'stkcod': b.STKCOD,
                    'supcod': b.SUPCOD,
                    'supname': b.SUPNAME or b.SUPCOD,
                    'amount': b.AMOUNT,
                    'vatamt': b.VATAMT,
                    'netamt': b.NETAMT
                } for b in bills
            ]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """Settings page for data synchronization and configuration."""
    if request.method == 'POST':
        try:
            engine = DBFSyncEngine()
            results = engine.sync_all()
            flash(f"✅ ซิงค์ข้อมูลสำเร็จ! (ข้อมูลสต็อก: {results['stmas']}, บัตรสต็อก: {results['stcrd']}, ผู้จำหน่าย: {results['apmas']}, รายการเคลื่อนไหว: {results['aptrn']})", "success")
        except Exception as e:
            flash(f"❌ ซิงค์ข้อมูลล้มเหลว: {str(e)}", "danger")
        return redirect(url_for('main.settings'))

    return render_template('settings.html', title="ตั้งค่าระบบ", active_page='settings')
