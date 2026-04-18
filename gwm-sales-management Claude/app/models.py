from app import db
from datetime import datetime

# ตารางกลางเชื่อมความสัมพันธ์ Model กับ Color (เพื่อให้ Dropdown แสดงเฉพาะสีที่รุ่นนั้นมี)
model_colors = db.Table('model_colors',
    db.Column('model_id', db.Integer, db.ForeignKey('master_car_models.model_id'), primary_key=True),
    db.Column('color_id', db.Integer, db.ForeignKey('master_colors.color_id'), primary_key=True)
)

class Brand(db.Model):
    __tablename__ = 'master_brands'
    brand_id = db.Column(db.Integer, primary_key=True)
    brand_name = db.Column(db.String(100), nullable=False, unique=True)
    
    # Relationship
    models = db.relationship('CarModel', backref='brand', lazy=True)
    variants = db.relationship('CarVariant', backref='brand', lazy=True)

class CarModel(db.Model):
    __tablename__ = 'master_car_models'
    model_id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('master_brands.brand_id'), nullable=False)
    model_name = db.Column(db.String(100), nullable=False)
    
    # Relationship
    variants = db.relationship('CarVariant', backref='car_model', lazy=True)
    colors = db.relationship('Color', secondary=model_colors, backref='models', lazy='dynamic')

class CarVariant(db.Model):
    __tablename__ = 'master_car_variants'
    variant_id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('master_brands.brand_id'), nullable=False)
    model_id = db.Column(db.Integer, db.ForeignKey('master_car_models.model_id'), nullable=False)
    variant_name = db.Column(db.String(150), nullable=False)
    
    # Relationship
    cars = db.relationship('Car', backref='variant', lazy=True)

class Color(db.Model):
    __tablename__ = 'master_colors'
    color_id = db.Column(db.Integer, primary_key=True)
    color_name = db.Column(db.String(100), nullable=False)
    color_type = db.Column(db.String(50)) # 'Exterior' หรือ 'Interior'

class Car(db.Model):
    __tablename__ = 'cars'
    vin_no = db.Column(db.String(50), primary_key=True) # เลขตัวถัง (Unique/PK)
    engine_no = db.Column(db.String(50), nullable=False) # เลขเครื่องยนต์
    variant_id = db.Column(db.Integer, db.ForeignKey('master_car_variants.variant_id'), nullable=False)
    
    # สีภายนอก/ภายใน
    color_ext_id = db.Column(db.Integer, db.ForeignKey('master_colors.color_id'))
    color_int_id = db.Column(db.Integer, db.ForeignKey('master_colors.color_id'))
    
    # ข้อมูลการรับรถ
    mileage_import = db.Column(db.Integer, default=0)
    receive_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # ข้อมูลเชื่อมโยงจาก Express
    express_doc_no = db.Column(db.String(50)) # เลขที่เอกสารใน Express
    express_stkcod = db.Column(db.String(50)) # รหัสสินค้าใน Express (เช่น 'รย')
    
    # ข้อมูลราคา
    cost_before_vat = db.Column(db.Float, default=0.0)
    vat_amount = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float, default=0.0)
    
    # สถานะ (เช่น 'In Stock', 'Reserved', 'Sold')
    status = db.Column(db.String(50), default='In Stock')

    # Relationship สำหรับดึงข้อมูลสี
    color_ext = db.relationship('Color', foreign_keys=[color_ext_id])
    color_int = db.relationship('Color', foreign_keys=[color_int_id])
