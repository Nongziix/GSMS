import customtkinter as ctk
from tkinter import messagebox
from theme import COLORS, FONTS, AppTheme
from config import get_db_connection
from db_service import DBService

class SearchLookupWindow(ctk.CTkToplevel):
    def __init__(self, parent, title, table, column, callback, filter_val=None):
        super().__init__(parent)
        self.title(f"ค้นหา {title}")
        self.geometry("500x500")
        self.callback = callback
        self.table = table
        self.column = column
        self.filter_val = filter_val
        self.attributes('-topmost', True)
        self.grab_set()
        self.after(200, self.lift); self.focus_set()

        ctk.CTkLabel(self, text=f"รายการ {title}", font=FONTS["subheading"]).pack(pady=10)
        f, self.search_ent = AppTheme.search_bar(self)
        f.pack(fill="x", padx=20, pady=5)
        self.search_ent.bind("<KeyRelease>", lambda e: self._load_data())
        self.listbox = ctk.CTkScrollableFrame(self)
        self.listbox.pack(fill="both", expand=True, padx=20, pady=10)
        self._load_data()

    def _load_data(self):
        for widget in self.listbox.winfo_children(): widget.destroy()
        search = self.search_ent.get().strip()
        conn = get_db_connection(); cur = conn.cursor()
        query = f"SELECT DISTINCT {self.column} FROM {self.table} WHERE {self.column} LIKE ?"
        params = [f"%{search}%"]
        if self.table == "master_colors" and self.filter_val:
            query += " AND color_type = ?"
            params.append(self.filter_val)
        cur.execute(query, params); rows = cur.fetchall(); conn.close()
        for r in rows:
            btn = ctk.CTkButton(self.listbox, text=r[0], fg_color="transparent", text_color=COLORS["text_dark"], 
                                anchor="w", hover_color=COLORS["primary_light"], height=35,
                                command=lambda val=r[0]: self._select(val))
            btn.pack(fill="x", pady=2)

    def _select(self, val):
        self.callback(val); self.destroy()

class ExpressPullWindow(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("ดึงข้อมูลจากบิล Express")
        self.geometry("1100x700")
        self.callback = callback
        self.configure(fg_color=COLORS["bg_app"])
        self.attributes('-topmost', True)
        self.grab_set()
        self.after(200, self.lift); self.focus_set()

        hdr = ctk.CTkFrame(self, fg_color=COLORS["bg_content"], height=65, corner_radius=0)
        hdr.pack(fill="x")
        ctk.CTkLabel(hdr, text="📦 รายการบิลซื้อรถ (จากระบบ Express)", font=FONTS["heading"], text_color=COLORS["primary"]).pack(side="left", padx=25)
        
        h_frame = ctk.CTkFrame(self, fg_color=COLORS["primary_light"], height=42, corner_radius=0)
        h_frame.pack(fill="x", pady=(15, 0))
        h_frame.pack_propagate(False)

        cols = [("เลขที่บิล", 140), ("วันที่", 100), ("เลขตัวถัง (VIN)", 180), ("รหัสสินค้า", 110), ("รายละเอียด", 320), ("จัดการ", 90)]
        for text, width in cols:
            ctk.CTkLabel(h_frame, text=text, width=width, font=FONTS["small_bold"], text_color=COLORS["primary"], anchor="w").pack(side="left", padx=10)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color=COLORS["bg_content"], corner_radius=0)
        self.scroll.pack(fill="both", expand=True)
        self._load_data()

    def _load_data(self):
        bills = DBService.get_car_purchase_bills()
        if not bills:
            ctk.CTkLabel(self.scroll, text="— ไม่พบข้อมูลบิลซื้อใหม่ใน Express —", font=FONTS["body"]).pack(pady=100)
            return
        for i, b in enumerate(bills):
            doc_num, doc_date, vin, stkdes, stkcod, total, vat, net = b
            bg = COLORS["bg_content"] if i % 2 == 0 else COLORS["table_stripe"]
            row = ctk.CTkFrame(self.scroll, fg_color=bg, height=52, corner_radius=0)
            row.pack(fill="x")
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=doc_num, width=140, font=FONTS["small"], anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=doc_date, width=100, font=FONTS["small"], anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=vin if vin else "-", width=180, font=FONTS["small_bold"], anchor="w", text_color=COLORS["info"]).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=stkcod, width=110, font=FONTS["small"], anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=stkdes, width=320, font=FONTS["small"], anchor="w").pack(side="left", padx=10)
            AppTheme.btn_primary(row, "เลือกบิล", lambda d=b: self._select(d), width=80, height=32).pack(side="right", padx=15, pady=10)

    def _select(self, b):
        doc_num, doc_date, vin, stkdes, stkcod, total, vat, net = b
        self.callback({'doc_num': doc_num, 'date': doc_date, 'vin': vin, 'desc': stkdes, 'stkcod': stkcod, 'total': total, 'vat': vat, 'net': net})
        self.destroy()

class BuyCarWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("รับรถเข้าสต็อก (GWM Sales BMS)")
        self.geometry("1100x950")
        self.attributes('-topmost', True)
        self.grab_set()
        
        self.brands_data = {}; self.models_data = {}; self.variants_data = {}
        self.ext_colors_data = {}; self.int_colors_data = {}

        header = ctk.CTkFrame(self, fg_color=COLORS["bg_content"], height=70, corner_radius=0); header.pack(fill="x")
        ctk.CTkLabel(header, text="📥  รับรถเข้าสต็อก (Purchase / Buy-in)", font=FONTS["heading"], text_color=COLORS["primary"]).pack(side="left", padx=25, pady=15)
        AppTheme.btn_primary(header, "🔄  ดึงข้อมูลจาก Express", self._pull_from_express, width=180, height=38).pack(side="right", padx=25)
        AppTheme.divider(self)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # --- Section 1: ข้อมูลบิล ---
        self._section_title("📋  ข้อมูลบิลซื้อจาก Express")
        self.exp_desc_label = ctk.CTkLabel(self.scroll, text="— ยังไม่ได้เลือกบิล —", font=FONTS["small_bold"], text_color=COLORS["info"])
        self.exp_desc_label.pack(anchor="w", padx=30, pady=(0, 10))
        
        r1 = AppTheme.form_row(self.scroll, "เลขที่บิล (ReadOnly)"); self.bill_no_ent = AppTheme.entry(r1)
        self.bill_no_ent.configure(state="disabled", fg_color="#F0F0F0"); self.bill_no_ent.pack(side="left", fill="x", expand=True)
        r2 = AppTheme.form_row(self.scroll, "รหัสสินค้า (ReadOnly)"); self.stkcod_ent = AppTheme.entry(r2)
        self.stkcod_ent.configure(state="disabled", fg_color="#F0F0F0"); self.stkcod_ent.pack(side="left", fill="x", expand=True)
        r3 = AppTheme.form_row(self.scroll, "วันที่ตามบิล"); self.receive_date = AppTheme.entry(r3)
        self.receive_date.pack(side="left", fill="x", expand=True)

        # --- Section 2: ข้อมูลรถ ---
        self._section_title("🚗  ข้อมูลตัวรถ")
        r4 = AppTheme.form_row(self.scroll, "เลขตัวถัง (VIN) *"); self.vin_entry = AppTheme.entry(r4, placeholder="ระบุเลขตัวถัง 17 หลัก")
        self.vin_entry.pack(side="left", fill="x", expand=True)
        r5 = AppTheme.form_row(self.scroll, "เลขเครื่องยนต์ *"); self.engine_entry = AppTheme.entry(r5, placeholder="ระบุเลขเครื่องยนต์")
        self.engine_entry.pack(side="left", fill="x", expand=True)

        # --- Section 3: Master Data ---
        self._section_title("🔍  ระบุรุ่นและสี")
        
        # ยี่ห้อ
        rb = AppTheme.form_row(self.scroll, "ยี่ห้อ (Brand) *")
        self.brand_cb = AppTheme.dropdown(rb, values=[], command=self._on_brand_change)
        self.brand_cb.pack(side="left", fill="x", expand=True)

        # รุ่นหลัก
        rm = AppTheme.form_row(self.scroll, "รุ่นหลัก (Model) *")
        self.model_cb = AppTheme.dropdown(rm, values=[], command=self._on_model_change)
        self.model_cb.pack(side="left", fill="x", expand=True)

        # รุ่นย่อย
        rv = AppTheme.form_row(self.scroll, "รุ่นย่อย (Variant) *")
        self.variant_cb = AppTheme.dropdown(rv, values=[])
        self.variant_cb.pack(side="left", fill="x", expand=True)

        # สีภายนอก
        re = AppTheme.form_row(self.scroll, "สีภายนอก")
        self.ext_color_cb = AppTheme.dropdown(re, values=[])
        self.ext_color_cb.pack(side="left", fill="x", expand=True)

        # สีภายใน
        ri = AppTheme.form_row(self.scroll, "สีภายใน")
        self.int_color_cb = AppTheme.dropdown(ri, values=[])
        self.int_color_cb.pack(side="left", fill="x", expand=True)

        # --- Section 4: ต้นทุนราคารถยนต์ ---
        self._section_title("💰  ต้นทุนราคารถยนต์")
        
        # ราคาก่อน Vat
        r9 = AppTheme.form_row(self.scroll, "ราคาก่อน Vat")
        self.total_ent = AppTheme.entry(r9, placeholder="0.00")
        self.total_ent.pack(side="left", fill="x", expand=True)
        self.total_ent.bind("<KeyRelease>", lambda e: self._calc_vat())

        # Vat 7%
        r10 = AppTheme.form_row(self.scroll, "ภาษีมูลค่าเพิ่ม (VAT 7%)")
        self.vat_ent = AppTheme.entry(r10, placeholder="0.00")
        self.vat_ent.pack(side="left", fill="x", expand=True)

        # ยอดสุทธิ
        r11 = AppTheme.form_row(self.scroll, "ยอดรวมสุทธิ (Net)")
        self.net_ent = AppTheme.entry(r11, placeholder="0.00")
        self.net_ent.pack(side="left", fill="x", expand=True)

        # เลขไมล์
        r12 = AppTheme.form_row(self.scroll, "เลขไมล์รับเข้า")
        self.mileage_entry = AppTheme.entry(r12)
        self.mileage_entry.insert(0, "0")
        self.mileage_entry.pack(side="left", fill="x", expand=True)

        # Footer
        footer = ctk.CTkFrame(self, fg_color=COLORS["bg_content"], height=80, corner_radius=0); footer.pack(fill="x", side="bottom")
        AppTheme.divider(footer)
        btn_row = ctk.CTkFrame(footer, fg_color="transparent"); btn_row.pack(fill="x", padx=25, pady=15)
        AppTheme.btn_secondary(btn_row, "ยกเลิก", self.destroy, 130, 44).pack(side="right", padx=(10, 0))
        AppTheme.btn_primary(btn_row, "💾  บันทึกข้อมูลรถเข้าสต็อก", self._save, 220, 44).pack(side="right")
        
        self._load_master_data()

    def _section_title(self, text):
        f = ctk.CTkFrame(self.scroll, fg_color="transparent"); f.pack(fill="x", padx=20, pady=(20, 8))
        ctk.CTkLabel(f, text=text, font=FONTS["body_bold"], text_color=COLORS["primary"]).pack(side="left")
        ctk.CTkFrame(f, fg_color=COLORS["border"], height=1).pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _calc_vat(self):
        try:
            val_str = self.total_ent.get().replace(",", "")
            if not val_str: return
            val = float(val_str)
            vat = val * 0.07
            net = val + vat
            self.vat_ent.delete(0, "end"); self.vat_ent.insert(0, f"{vat:,.2f}")
            self.net_ent.delete(0, "end"); self.net_ent.insert(0, f"{net:,.2f}")
        except: pass

    def _load_master_data(self):
        try:
            brands = DBService.get_all_brands()
            self.brands_data = {name: id for id, name in brands}
            self.brand_cb.configure(values=list(self.brands_data.keys()))
            ext_colors = DBService.get_colors("Exterior")
            self.ext_colors_data = {name: id for id, name in ext_colors}
            self.ext_color_cb.configure(values=list(self.ext_colors_data.keys()))
            int_colors = DBService.get_colors("Interior")
            self.int_colors_data = {name: id for id, name in int_colors}
            self.int_color_cb.configure(values=list(self.int_colors_data.keys()))
        except Exception as e: print(f"Error master data: {e}")

    def _on_brand_change(self, brand_name):
        bid = self.brands_data.get(brand_name)
        if bid:
            models = DBService.get_models_by_brand(bid)
            self.models_data = {name: id for id, name in models}
            self.model_cb.configure(values=list(self.models_data.keys())); self.model_cb.set("")
            self.variant_cb.configure(values=[]); self.variant_cb.set("")
        else: self.model_cb.configure(values=[]); self.variant_cb.configure(values=[])

    def _on_model_change(self, model_name):
        mid = self.models_data.get(model_name)
        if mid:
            variants = DBService.get_variants_by_model(mid)
            self.variants_data = {name: id for id, name in variants}
            self.variant_cb.configure(values=list(self.variants_data.keys())); self.variant_cb.set("")
        else: self.variant_cb.configure(values=[])

    def _pull_from_express(self): ExpressPullWindow(self, self._fill_from_express)

    def _fill_from_express(self, d):
        self.exp_desc_label.configure(text=f"📌 ข้อมูลจาก Express: {d['desc']}")
        for ent, val in [(self.bill_no_ent, d['doc_num']), (self.stkcod_ent, d['stkcod'])]:
            ent.configure(state="normal"); ent.delete(0, "end"); ent.insert(0, val); ent.configure(state="disabled")
        
        self.total_ent.delete(0, "end"); self.total_ent.insert(0, f"{d['total']:,.2f}")
        self.vat_ent.delete(0, "end"); self.vat_ent.insert(0, f"{d['vat']:,.2f}")
        self.net_ent.delete(0, "end"); self.net_ent.insert(0, f"{d['net']:,.2f}")
        
        self.vin_entry.delete(0, "end"); self.vin_entry.insert(0, d['vin'] if d['vin'] else "")
        self.receive_date.delete(0, "end"); self.receive_date.insert(0, d['date'])
        self.vin_entry.focus()

    def _save(self):
        vin, eng, v_name = self.vin_entry.get().strip().upper(), self.engine_entry.get().strip().upper(), self.variant_cb.get().strip()
        if not self.bill_no_ent.get(): messagebox.showwarning("เตือน", "กรุณาดึงข้อมูลจากบิล Express ก่อนบันทึก"); return
        if not vin or len(vin) != 17 or not v_name or not eng: 
            messagebox.showwarning("ข้อมูลไม่ครบ", "กรุณาระบุเลขตัวถัง (17 หลัก), เลขเครื่องยนต์ และเลือกรุ่นรถ"); return
        try:
            v_id = self.variants_data.get(v_name)
            ext_id = self.ext_colors_data.get(self.ext_color_cb.get().strip())
            int_id = self.int_colors_data.get(self.int_color_cb.get().strip())
            if not v_id: messagebox.showerror("Error", "กรุณาเลือกรุ่นย่อยให้ถูกต้อง"); return
            conn = get_db_connection(); cur = conn.cursor()
            total = float(self.total_ent.get().replace(",", "") or 0)
            vat = float(self.vat_ent.get().replace(",", "") or 0)
            net = float(self.net_ent.get().replace(",", "") or 0)
            cur.execute('''
                INSERT INTO cars (import_type, vin_no, engine_no, variant_id, color_ext_id, color_int_id, 
                                 express_doc_no, express_stkcod, cost_before_vat, vat_amount, net_amount, 
                                 mileage_import, cost, receive_date, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'Available')
            ''', ("Purchase", vin, eng, v_id, ext_id, int_id, self.bill_no_ent.get(), self.stkcod_ent.get(), 
                  total, vat, net, int(self.mileage_entry.get() or 0), net, self.receive_date.get()))
            conn.commit(); conn.close(); messagebox.showinfo("สำเร็จ ✅", f"บันทึกรถเลขตัวถัง {vin} เรียบร้อย"); self.destroy()
        except Exception as e: messagebox.showerror("Error", f"บันทึกไม่ได้: {e}")
