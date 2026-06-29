from datetime import datetime
import json

HAS_WEASYPRINT = False

def _get_weasyprint():
    """Lazy import WeasyPrint — only loaded when PDF is actually generated."""
    try:
        from weasyprint import HTML as _HTML
        globals()["_WHTML"] = _HTML
        globals()["HAS_WEASYPRINT"] = True
        return _HTML
    except Exception:
        return None


def format_version(v):
    if v is None or v == 0:
        return "V0"
    num = float(v)
    if num % 1 == 0:
        return f"V{int(num)}"
    return f"V{num:.2f}"


def _snap_val(snap, key, default=""):
    """Safely extract a value from contract_snapshot (JSON field) or snapshot dict."""
    if not snap:
        return default
    if isinstance(snap, str):
        try:
            snap = json.loads(snap)
        except (json.JSONDecodeError, TypeError):
            return default
    return snap.get(key, default)


def render_process_sheet(sheet, contract, items) -> bytes:
    """Render a process sheet to PDF bytes.

    Args:
        sheet: ProcessSheet model instance
        contract: Contract model instance (for top-level info, fallback)
        items: list of ProcessSheetItem (NOT ContractItem)
    """
    detail = sheet.detail_data or {}
    snap = sheet.contract_snapshot or {}

    # ── Item rows (from ProcessSheetItem) ──
    item_rows = ""
    for i in items:
        spec_name = ""
        if i.spec:
            spec_name = i.spec.spec_description or i.spec.spec_name or ""
        packaging = i.packaging_type or ""
        pressed = "压花" if i.is_pressed else ""
        p_remark = i.process_remark or ""
        item_rows += f"""
        <tr>
            <td style="text-align:center">{i.line_no}</td>
            <td>{spec_name}</td>
            <td>{i.pattern_code or ''}</td>
            <td>{i.color_a or ''}{' / ' + (i.color_b or '') if i.color_b else ''}</td>
            <td style="text-align:center">{packaging}</td>
            <td style="text-align:center">{pressed}</td>
            <td style="text-align:right">{i.qty or 0}</td>
            <td>{p_remark}</td>
            <td>{i.remark or ''}</td>
        </tr>"""

    # ── Accessories from detail_data ──
    acc_labels = {1: "包贴彩卡", 2: "彩卡", 3: "钢丝袋", 4: "真空包", 5: "辅料", 6: "辅料"}
    accessories_html = ""
    for idx in range(1, 7):
        desc = detail.get(f"accessory_desc_{idx}", "") or ""
        size = detail.get(f"accessory_size_{idx}", "") or ""
        qty = detail.get(f"accessory_qty_{idx}", "") or ""
        if desc or size or qty:
            label = desc or acc_labels.get(idx, f"辅料{idx}")
            accessories_html += f"<tr><td>{label}</td><td>{size}</td><td style='text-align:right'>{qty}</td></tr>"

    # Washing / origin labels from detail_data
    for label_list_key, label_name in [("washing_labels", "洗标"), ("origin_labels", "产地标")]:
        label_list = detail.get(label_list_key, [])
        if label_list:
            for lb in label_list:
                if lb.get("size") or lb.get("qty") or lb.get("images"):
                    accessories_html += f"<tr><td>{label_name}</td><td>{lb.get('size', '')}</td><td style='text-align:right'>{lb.get('qty', '')}</td></tr>"

    # ── Notes sections ──
    def _notes_html(prefix, count):
        items_list = []
        for i in range(1, count + 1):
            val = detail.get(f"{prefix}_{i}", "") or ""
            if val.strip():
                items_list.append(f"<li>{val.strip()}</li>")
        return "".join(items_list)

    tech_notes = _notes_html("tech_note", 10)
    pack_notes = _notes_html("pack_note", 5)
    box_notes = _notes_html("box_note", 3)

    # ── Version and date (top right) ──
    version_str = format_version(sheet.confirm_version_no)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Contract info from snapshot or contract object ──
    customer_name = _snap_val(snap, "customer_name", contract.customer.name if contract and contract.customer else "")
    contract_no = _snap_val(snap, "contract_no", contract.contract_no if contract else "")
    contract_date = _snap_val(snap, "contract_date", str(contract.contract_date) if contract and contract.contract_date else "")
    # total_amount: try snapshot first, then contract.total_amount
    total_amount = "0.00"
    snap_amount = _snap_val(snap, "total_amount", None)
    if snap_amount is not None:
        try:
            total_amount = f"{float(snap_amount):.2f}"
        except (ValueError, TypeError):
            total_amount = "0.00"
    elif contract and contract.total_amount:
        total_amount = f"{float(contract.total_amount):.2f}"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ margin: 10mm 14mm; size: A4; }}
    @page {{ @bottom-center {{ content: counter(page) " / " counter(pages); font-size: 7pt; color: #999; }} }}

    body {{
        font-family: 'SimSun', 'Noto Serif CJK SC', 'Source Han Serif SC', 'STSong', 'AR PL New Sung', 'FangSong', serif;
        font-size: 9pt;
        color: #222;
        line-height: 1.5;
    }}

    .header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 2px solid #222;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }}
    .header-left h1 {{
        margin: 0;
        font-size: 20pt;
        font-weight: bold;
        letter-spacing: 4px;
    }}
    .header-left .company {{
        font-size: 8pt;
        color: #666;
        margin-top: 1px;
    }}
    .header-right {{
        text-align: right;
        font-size: 8pt;
        color: #333;
    }}
    .header-right .ver {{
        font-size: 13pt;
        font-weight: bold;
        color: #c00;
    }}
    .header-right .date {{
        font-size: 7.5pt;
        color: #999;
        margin-top: 1px;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 4px 0;
    }}
    td, th {{
        border: 1px solid #333;
        padding: 3px 5px;
        text-align: left;
        vertical-align: top;
    }}
    th {{
        background: #f0f0f0;
        font-weight: bold;
        font-size: 8.5pt;
        white-space: nowrap;
    }}

    .section-title {{
        font-weight: bold;
        margin-top: 10px;
        margin-bottom: 3px;
        font-size: 10pt;
        background: #e8e8e8;
        padding: 4px 8px;
        border-left: 3px solid #c00;
    }}

    ul {{
        margin: 3px 0;
        padding-left: 20px;
    }}
    li {{
        margin: 1px 0;
        font-size: 8.5pt;
    }}

    .info-table th {{
        width: 12%;
    }}
    .info-table td {{
        width: 23%;
    }}

    .item-table th {{
        background: #d9d9d9;
        font-size: 8pt;
        text-align: center;
    }}
    .item-table td {{
        font-size: 8.5pt;
    }}

    .footer-note {{
        margin-top: 14px;
        padding-top: 6px;
        border-top: 1px solid #ccc;
        color: #999;
        font-size: 7pt;
        text-align: center;
    }}

    .empty-row td {{
        color: #aaa;
        text-align: center;
        font-size: 8pt;
    }}
</style>
</head>
<body>

    <div class="header">
        <div class="header-left">
            <h1>生产工艺单</h1>
            <div class="company">嘉元瑞通工厂管理系统</div>
        </div>
        <div class="header-right">
            <div class="ver">{version_str}</div>
            <div>工艺版本</div>
            <div class="date">打印: {now_str}</div>
        </div>
    </div>

    <!-- Basic Info -->
    <table class="info-table">
        <tr>
            <th>工艺单号</th><td>{sheet.sheet_no}</td>
            <th>合同号</th><td>{contract_no}</td>
        </tr>
        <tr>
            <th>客户名称</th><td>{customer_name}</td>
            <th>合同日期</th><td>{contract_date}</td>
        </tr>
        <tr>
            <th>交货日期</th>
            <td>{items[0].delivery_date if items and items[0].delivery_date else detail.get('delivery_date', '') or ''}</td>
            <th>合同金额</th>
            <td>¥{total_amount}</td>
        </tr>
    </table>

    <!-- Item Details -->
    <div class="section-title">行项目明细</div>
    <table class="item-table">
        <tr>
            <th style="width:4%">行号</th>
            <th style="width:16%">毛毯规格</th>
            <th style="width:10%">花型代码</th>
            <th style="width:12%">颜色（A/B面）</th>
            <th style="width:8%">包装方式</th>
            <th style="width:5%">压花</th>
            <th style="width:6%">数量</th>
            <th style="width:16%">工艺备注</th>
            <th style="width:13%">备注</th>
        </tr>
        {item_rows}
    </table>

    <!-- Binding and Emboss -->
    <table class="info-table">
        <tr>
            <th style="width:12%">包边材料</th>
            <td style="width:23%">{detail.get('binding_material', '') or ''}</td>
            <th style="width:12%">包边宽度</th>
            <td style="width:23%">{detail.get('binding_width', '') or ''}</td>
            <th style="width:10%">色号</th>
            <td style="width:20%">{detail.get('binding_color_no', '') or ''}</td>
        </tr>
        <tr>
            <th>压花型号</th>
            <td colspan="5">{detail.get('emboss_model', '') or ''}</td>
        </tr>
    </table>

    <!-- Accessories -->
    <div class="section-title">辅料明细</div>
    <table>
        <tr>
            <th style="width:30%">名称</th>
            <th style="width:40%">规格</th>
            <th style="width:15%">数量</th>
        </tr>
        {accessories_html or '<tr class="empty-row"><td colspan="3">无</td></tr>'}
    </table>

    <!-- Technical Notes -->
    <div class="section-title">工艺说明</div>
    <ul>{tech_notes or '<li style="color:#999">无</li>'}</ul>

    <!-- Packaging Notes -->
    <div class="section-title">包装说明</div>
    <ul>{pack_notes or '<li style="color:#999">无</li>'}</ul>

    <!-- Box Notes -->
    <div class="section-title">箱单说明</div>
    <ul>{box_notes or '<li style="color:#999">无</li>'}</ul>

    <div class="footer-note">
        工艺单号: {sheet.sheet_no} &nbsp;|&nbsp; 版本: {version_str} &nbsp;|&nbsp; 打印时间: {now_str} &nbsp;|&nbsp; 嘉元瑞通
    </div>

</body>
</html>"""

    WHTML = _get_weasyprint()
    if not WHTML:
        raise RuntimeError(
            "WeasyPrint not available. Run: pip install weasyprint\n"
            "On macOS also install system deps: brew install pango libffi"
        )
    return WHTML(string=html).write_pdf()
