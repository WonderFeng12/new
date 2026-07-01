import os
from datetime import datetime
import json

from app.config import settings

HAS_WEASYPRINT = False

UPLOAD_DIR = settings.UPLOAD_DIR


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
    if not snap:
        return default
    if isinstance(snap, str):
        try:
            snap = json.loads(snap)
        except (json.JSONDecodeError, TypeError):
            return default
    return snap.get(key, default)


def _resolve_image_path(relative_path):
    if not relative_path:
        return ""
    path = relative_path
    if path.startswith("/uploads/"):
        path = path[len("/uploads/"):]
    abs_path = os.path.join(UPLOAD_DIR, path)
    if os.path.exists(abs_path):
        return f"file://{abs_path}"
    return ""


def _img_tag(path, alt="", w=60, h=60):
    resolved = _resolve_image_path(path)
    if not resolved:
        return ""
    return f'<img src="{resolved}" alt="{alt}" style="max-width:{w}px;max-height:{h}px;object-fit:contain;border:1px solid #ccc;border-radius:2px;margin:1px">'


def _img_cell(paths, alt_prefix="", size=55):
    tags = []
    for p in paths:
        if p:
            t = _img_tag(p, alt_prefix, w=size, h=size)
            if t:
                tags.append(t)
    if not tags:
        return ""
    return "".join(tags)


def _notes_html(data, prefix, count):
    items_list = []
    for i in range(1, count + 1):
        val = data.get(f"{prefix}_{i}", "") or ""
        if val.strip():
            items_list.append(f"<li>{val.strip()}</li>")
    return "".join(items_list)


def render_process_sheet(sheet, contract, items) -> bytes:
    detail = sheet.detail_data or {}
    snap = sheet.contract_snapshot or {}

    # ── Item rows and image rows ──
    item_rows = ""
    for i in items:
        spec_name = ""
        if i.spec:
            spec_name = i.spec.spec_description or i.spec.spec_name or ""
        packaging = i.packaging_type or ""
        pressed = "压花" if i.is_pressed else ""
        p_remark = i.process_remark or ""

        # Pattern images + info
        pattern_data = i.pattern_data or []
        if isinstance(pattern_data, str):
            try:
                pattern_data = json.loads(pattern_data)
            except (json.JSONDecodeError, TypeError):
                pattern_data = []

        # Filter to items that have images
        pattern_items = [p for p in pattern_data if isinstance(p, dict) and p.get("image")]

        # Determine if composite spec
        is_composite = i.spec and i.spec.layer_type and "复合" in i.spec.layer_type

        # Build pattern grid (3 columns)
        pattern_grid_html = ""
        pressed_path = getattr(i, "pressed_image", None) or ""

        if pattern_items:
            if is_composite:
                # Group as A/B pairs: (1A,1B), (2A,2B), (3A,3B)...
                pairs = [pattern_items[j:j+2] for j in range(0, len(pattern_items), 2)]
                groups = pairs
            else:
                # Each item is its own group
                groups = [[p] for p in pattern_items]

            pattern_grid_html = '<table style="width:100%;border-collapse:collapse">'
            for row_start in range(0, len(groups), 3):
                row_groups = groups[row_start:row_start + 3]
                pattern_grid_html += '<tr>'
                for gi, grp in enumerate(row_groups):
                    pattern_grid_html += '<td style="width:33%;border:none;vertical-align:top;text-align:center;padding:3px'
                    if gi > 0:
                        pattern_grid_html += ';border-left:1px dashed #ccc;padding-left:6px'
                    pattern_grid_html += '">'
                    for pd_item in grp:
                        img = pd_item.get("image", "")
                        code = pd_item.get("code", "") or ""
                        color = pd_item.get("color", "") or ""
                        binding_no = pd_item.get("binding_color_no", "") or ""
                        info_parts = []
                        if code:
                            info_parts.append(code)
                        if color:
                            info_parts.append(f"颜色:{color}")
                        if binding_no:
                            info_parts.append(f"色号:{binding_no}")
                        info_str = " | ".join(info_parts)
                        pattern_grid_html += '<div style="display:inline-block;text-align:center;margin:2px 4px;vertical-align:top">'
                        pattern_grid_html += _img_tag(img, "花型", w=86, h=86)
                        if info_str:
                            pattern_grid_html += f'<div style="font-size:6pt;color:#555;line-height:1.1;word-wrap:break-word;max-width:55px">{info_str}</div>'
                        pattern_grid_html += '</div>'
                    pattern_grid_html += '</td>'
                # Fill remaining columns
                for _ in range(3 - len(row_groups)):
                    pattern_grid_html += '<td style="width:33%;border:none"></td>'
                pattern_grid_html += '</tr>'
            # Last row: pressed image
            if pressed_path:
                pattern_grid_html += f'<tr><td colspan="3" style="border:none;text-align:center;padding-top:4px;border-top:1px solid #eee"><span style="font-size:7pt;color:#888">压花:</span>{_img_tag(pressed_path, "压花", w=86, h=86)}</td></tr>'
            pattern_grid_html += '</table>'

        # A/B side images
        a_images = []
        for img_key in ["image_a_1", "image_a_2", "image_a_3"]:
            val = getattr(i, img_key, None) or ""
            if val:
                a_images.append(val)
        b_images = []
        for img_key in ["image_b_1", "image_b_2", "image_b_3"]:
            val = getattr(i, img_key, None) or ""
            if val:
                b_images.append(val)

        # Build image row
        imgs_html = ""
        if pattern_grid_html:
            imgs_html += pattern_grid_html
        if a_images:
            imgs_html += f'<div style="margin-top:3px"><span style="font-size:7.5pt;color:#888">A面:</span>{_img_cell(a_images, "A面")}</div>'
        if b_images:
            imgs_html += f'<div style="margin-top:2px"><span style="font-size:7.5pt;color:#888">B面:</span>{_img_cell(b_images, "B面")}</div>'

        if imgs_html:
            imgs_html = f'<tr><td colspan="6" style="padding:2px 5px;border-top:none">{imgs_html}</td></tr>'

        item_rows += f"""
        <tr>
            <td style="text-align:center">{i.line_no}</td>
            <td>{spec_name}</td>
            <td style="text-align:center">{packaging}</td>
            <td style="text-align:center">{pressed}</td>
            <td style="text-align:right">{float(i.qty or 0):.1f}</td>
            <td>{p_remark}</td>
        </tr>{imgs_html}"""

    # ── Accessories grid ──
    acc_labels = {1: "包贴彩卡", 2: "彩卡", 3: "钢丝袋", 4: "真空包", 5: "辅料1", 6: "辅料2"}

    def _acc_cell(idx):
        desc = detail.get(f"accessory_desc_{idx}", "") or ""
        size = detail.get(f"accessory_size_{idx}", "") or ""
        qty = detail.get(f"accessory_qty_{idx}", "") or ""
        img_html = _acc_images(detail, idx)
        if not desc and not size and not qty and not img_html:
            return ""
        label = desc or acc_labels.get(idx, f"辅料{idx}")
        cell = f'<strong style="font-size:7.5pt">{label}</strong>'
        parts = []
        if qty:
            parts.append(qty)
        if size:
            parts.append(size)
        if parts:
            cell += f'<br><span style="font-size:7pt;color:#666">{" | ".join(parts)}</span>'
        if img_html:
            cell += f"<br>{img_html}"
        return cell

    def _label_cell(label_name, label_item):
        img_html = _img_cell(label_item.get("images", []), label_name)
        size = str(label_item.get("size", "") or "")
        qty = str(label_item.get("qty", "") or "")
        if not size and not qty and not img_html:
            return ""
        cell = f'<strong style="font-size:7.5pt">{label_name}</strong>'
        parts = []
        if qty:
            parts.append(qty)
        if size:
            parts.append(size)
        if parts:
            cell += f'<br><span style="font-size:7pt;color:#666">{" | ".join(parts)}</span>'
        if img_html:
            cell += f"<br>{img_html}"
        return cell

    # 包贴彩卡 (idx 1) — spans 2 cols and 2 rows
    c1 = _acc_cell(1)
    baotie_idx = 1
    if not c1:
        # Fallback: search other indices for 包贴彩卡 data
        for idx in range(2, 7):
            desc = detail.get(f"accessory_desc_{idx}", "") or ""
            if "包贴彩卡" in desc or "包贴" in desc:
                c1 = _acc_cell(idx)
                baotie_idx = idx
                break
    has_baotie = bool(c1)

    # Row 1: 洗标 | 产地标 | 包贴彩卡(colspan=2, rowspan=2)
    row1_leading = []
    for lb in (detail.get("washing_labels") or []):
        c = _label_cell("洗标", lb)
        if c:
            row1_leading.append(c)
    for lb in (detail.get("origin_labels") or []):
        c = _label_cell("产地标", lb)
        if c:
            row1_leading.append(c)

    # Row 2: 钢丝袋 | 真空包 (最多2个), skip baotie_idx to avoid duplication
    row2_cells = []
    for idx in [3, 4, 2, 5, 6]:
        if idx == baotie_idx:
            continue
        c = _acc_cell(idx)
        if c:
            row2_cells.append(c)
            if len(row2_cells) >= 2:
                break

    accessories_html = ""
    if row1_leading or has_baotie or row2_cells:
        rows_html = ""
        col_w = 25

        # Row 1: 洗标/产地标 (up to 2 cols) | 包贴彩卡 (colspan=2, rowspan=2)
        r1 = ""
        for c in row1_leading[:2]:
            r1 += f'<td style="width:{col_w}%;padding:3px 6px;border:1px solid #333;vertical-align:top">{c}</td>'
        r1 += f'<td style="width:{col_w}%;padding:3px 6px;border:1px solid #333"></td>' * (2 - len(row1_leading[:2]))
        bt = c1 if has_baotie else ""
        r1 += f'<td colspan="2" rowspan="2" style="width:50%;padding:3px 6px;border:1px solid #333;vertical-align:top">{bt}</td>'
        rows_html += f"<tr>{r1}</tr>"

        # Row 2: 钢丝袋 | 真空包 (cols 1-2, cols 3-4 occupied by rowspan)
        r2 = ""
        for c in row2_cells[:2]:
            r2 += f'<td style="width:{col_w}%;padding:3px 6px;border:1px solid #333;vertical-align:top">{c}</td>'
        r2 += f'<td style="width:{col_w}%;padding:3px 6px;border:1px solid #333"></td>' * (2 - len(row2_cells[:2]))
        rows_html += f"<tr>{r2}</tr>"

        accessories_html = f'<table style="width:100%;border-collapse:collapse">{rows_html}</table>'

    # ── Notes ──
    tech_notes = _notes_html(detail, "tech_note", 21)
    pack_notes = _notes_html(detail, "pack_note", 21)
    box_notes = _notes_html(detail, "box_note", 21)

    # ── Version and date ──
    version_str = format_version(sheet.confirm_version_no)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # ── Contract info ──
    customer_name = _snap_val(snap, "customer_name", contract.customer.name if contract and contract.customer else "")
    contract_no = _snap_val(snap, "contract_no", contract.contract_no if contract else "")
    contract_date = _snap_val(snap, "contract_date", str(contract.contract_date) if contract and contract.contract_date else "")
    delivery_date = items[0].delivery_date if items and items[0].delivery_date else detail.get("delivery_date", "") or ""

    # ── Process description (same logic as frontend: spec_name + 经编印花 + pressed + 毛毯-包装方式) ──
    first_item = items[0] if items else None
    process_desc = ""
    if first_item:
        sn = first_item.spec.spec_name if first_item.spec else ""
        pressed_flag = "压花" if first_item.is_pressed else ""
        pkg = first_item.packaging_type or ""
        process_desc = f"{sn}经编印花{pressed_flag}毛毯-{pkg}" if sn else ""

    # ── Binding / emboss ──
    binding_material = detail.get("binding_material", "") or ""
    binding_width = detail.get("binding_width", "") or ""
    emboss_model = detail.get("emboss_model", "") or ""

    # Pressed image name from first item that has one
    pressed_name = ""
    for i in items:
        pn = getattr(i, "pressed_image_name", None) or ""
        if pn:
            pressed_name = pn
            break

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ margin: 8mm 12mm; size: A4; }}
    @page {{ @bottom-center {{ content: counter(page) " / " counter(pages); font-size: 7pt; color: #999; }} }}

    body {{
        font-family: 'SimSun', 'Noto Serif CJK SC', 'Source Han Serif SC', 'STSong', 'AR PL New Sung', 'FangSong', serif;
        font-size: 8.5pt;
        color: #222;
        line-height: 1.35;
    }}

    .header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        border-bottom: 2px solid #222;
        padding-bottom: 4px;
        margin-bottom: 6px;
    }}
    .header-left h1 {{
        margin: 0;
        font-size: 16pt;
        font-weight: bold;
        letter-spacing: 2px;
    }}
    .header-left .company {{
        font-size: 7pt;
        color: #666;
    }}
    .header-right {{
        text-align: right;
        font-size: 7.5pt;
        color: #333;
    }}
    .header-right .ver {{
        font-size: 11pt;
        font-weight: bold;
        color: #c00;
    }}
    .header-right .date {{
        font-size: 7pt;
        color: #999;
    }}

    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 3px 0;
    }}
    td, th {{
        border: 1px solid #333;
        padding: 2px 4px;
        text-align: left;
        vertical-align: middle;
    }}
    th {{
        background: #f0f0f0;
        font-weight: bold;
        font-size: 8pt;
        white-space: nowrap;
    }}

    .section-title {{
        font-weight: bold;
        margin-top: 6px;
        margin-bottom: 2px;
        font-size: 9pt;
        background: #e8e8e8;
        padding: 2px 6px;
        border-left: 3px solid #c00;
    }}

    ul {{
        margin: 2px 0;
        padding-left: 16px;
    }}
    li {{
        margin: 0;
        font-size: 7.5pt;
        line-height: 1.3;
    }}

    .info-table th {{
        width: 10%;
        font-size: 7.5pt;
    }}
    .info-table td {{
        width: 23%;
        font-size: 7.5pt;
    }}

    .item-table th {{
        background: #d9d9d9;
        font-size: 7.5pt;
        text-align: center;
    }}
    .item-table td {{
        font-size: 8pt;
    }}

    .footer-note {{
        margin-top: 8px;
        padding-top: 4px;
        border-top: 1px solid #ccc;
        color: #999;
        font-size: 6.5pt;
        text-align: center;
    }}

    .compact-info {{
        display: flex;
        flex-wrap: wrap;
        gap: 4px 16px;
        padding: 3px 6px;
        border: 1px solid #333;
        font-size: 7.5pt;
        margin: 3px 0;
    }}
    .compact-info span {{
        white-space: nowrap;
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
            <th>客户名称</th><td>{customer_name}</td>
        </tr>
        <tr>
            <th>合同日期</th><td>{contract_date}</td>
            <th>交货日期</th><td>{delivery_date}</td>
            <td colspan="2" style="font-size:7.5pt">{process_desc}</td>
        </tr>
    </table>

    <!-- Item Details -->
    <div class="section-title">行项目明细</div>
    <table class="item-table">
        <tr>
            <th style="width:4%">行号</th>
            <th style="width:28%">毛毯规格</th>
            <th style="width:9%">包装方式</th>
            <th style="width:6%">压花</th>
            <th style="width:8%">数量</th>
            <th style="width:20%">工艺备注</th>
        </tr>
        {item_rows}
    </table>

    <!-- Binding / Emboss (compact inline) -->
    <div class="compact-info">
        <span><strong>包边材料:</strong> {binding_material or '—'}</span>
        <span><strong>包边宽度:</strong> {binding_width or '—'}</span>
        <span><strong>压花型号:</strong> {pressed_name or emboss_model or '—'}</span>
    </div>

    <!-- Accessories Grid -->
    {accessories_html and f'<div class="section-title">辅料明细</div>' or ''}
    {accessories_html}

    <!-- Technical / Packaging / Box Notes in 2-column layout -->
    <div style="display:flex;gap:12px;margin-top:4px">
        <div style="flex:3">
            {(tech_notes) and f'<div class="section-title">工艺说明</div><ul>{tech_notes}</ul>' or ''}
            {(pack_notes) and f'<div class="section-title" style="margin-top:3px">包装说明</div><ul>{pack_notes}</ul>' or ''}
            {(box_notes) and f'<div class="section-title" style="margin-top:3px">箱单说明</div><ul>{box_notes}</ul>' or ''}
        </div>
    </div>

    <div class="footer-note">
        工艺单号: {sheet.sheet_no} | 版本: {version_str} | 打印时间: {now_str} | 嘉元瑞通
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


def _acc_images(detail, idx):
    """Get accessory images for a given index (1-6)."""
    key = f"accessory_images_{idx}"
    val = detail.get(key)
    if not val:
        return ""
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return ""
    if isinstance(val, list):
        return _img_cell(val[:3], size=82)
    return ""
