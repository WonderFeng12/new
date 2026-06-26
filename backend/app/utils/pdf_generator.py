try:
    from weasyprint import HTML
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False


def render_process_sheet(sheet, contract, items) -> bytes:
    item_rows = ""
    for i in items:
        item_rows += f"""
        <tr>
            <td>{i.line_no}</td>
            <td>{i.pattern_code or ''}</td>
            <td>{i.color_a or ''} / {i.color_b or ''}</td>
            <td>{i.qty}</td>
            <td>{i.unit_price}</td>
            <td>{i.amount}</td>
            <td>{i.remark or ''}</td>
        </tr>"""

    accessories_html = ""
    for idx in range(1, 7):
        desc = getattr(contract, f"accessory_desc_{idx}", "") or ""
        size = getattr(contract, f"accessory_size_{idx}", "") or ""
        qty = getattr(contract, f"accessory_qty_{idx}", "") or ""
        if desc:
            accessories_html += f"<tr><td>{desc}</td><td>{size}</td><td>{qty}</td></tr>"

    pack_notes = "".join(
        f"<li>{getattr(contract, f'pack_note_{i}', '') or ''}</li>"
        for i in range(1, 6)
        if getattr(contract, f"pack_note_{i}", "")
    )

    box_notes = "".join(
        f"<li>{getattr(contract, f'box_note_{i}', '') or ''}</li>"
        for i in range(1, 4)
        if getattr(contract, f"box_note_{i}", "")
    )

    tech_notes = "".join(
        f"<li>{getattr(contract, f'tech_note_{i}', '') or ''}</li>"
        for i in range(1, 11)
        if getattr(contract, f"tech_note_{i}", "")
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ margin: 15mm; size: A4; }}
    body {{ font-family: 'SimSun', 'Noto Serif CJK SC', serif; font-size: 10pt; }}
    h1 {{ text-align: center; font-size: 16pt; margin-bottom: 4px; }}
    .subtitle {{ text-align: center; font-size: 9pt; color: #666; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 8px 0; }}
    td, th {{ border: 1px solid #333; padding: 4px 6px; text-align: left; }}
    th {{ background: #f0f0f0; }}
    .section-title {{ font-weight: bold; margin-top: 12px; margin-bottom: 4px; font-size: 11pt; }}
    .version-note {{ margin-top: 16px; color: #666; font-size: 8pt; text-align: right; }}
    ul {{ margin: 4px 0; padding-left: 20px; }}
</style>
</head>
<body>
    <h1>嘉元瑞通 · 生产工艺单</h1>
    <div class="subtitle">打印日期: {contract.contract_date}</div>

    <table>
        <tr><th style="width:20%">工艺单号</th><td style="width:30%">{sheet.sheet_no}</td><th style="width:20%">合同号</th><td style="width:30%">{contract.contract_no}</td></tr>
        <tr><th>客户</th><td>{contract.customer.name if contract.customer else ''}</td><th>合同日期</th><td>{contract.contract_date}</td></tr>
        <tr><th>规格描述</th><td colspan="3">{contract.spec_description or ''}</td></tr>
        <tr><th>包边材料</th><td>{contract.binding_material or ''}</td><th>包边宽度</th><td>{contract.binding_width or ''}</td></tr>
        <tr><th>包边色号</th><td>{contract.binding_color_no or ''}</td><th>压花模型</th><td>{contract.emboss_model or ''}</td></tr>
        <tr><th>是否压花</th><td>{'是' if contract.is_pressed else '否'}</td><th>包装方式</th><td>{contract.packaging_type or ''}</td></tr>
        <tr><th>交货日期</th><td>{contract.delivery_date or ''}</td><th>总金额</th><td>¥{float(contract.total_amount or 0):.2f}</td></tr>
    </table>

    <div class="section-title">花型行项目</div>
    <table>
        <tr><th>行号</th><th>花型代码</th><th>颜色</th><th>数量</th><th>单价</th><th>金额</th><th>备注</th></tr>
        {item_rows}
    </table>

    <div class="section-title">辅料信息</div>
    <table>
        <tr><th>名称</th><th>规格</th><th>数量</th></tr>
        {accessories_html}
    </table>

    <div class="section-title">工艺说明</div>
    <ul>{tech_notes}</ul>

    <div class="section-title">包装说明</div>
    <ul>{pack_notes}</ul>

    <div class="section-title">箱单说明</div>
    <ul>{box_notes}</ul>

    <div class="version-note">
        ⓘ 本工艺单基于 {contract.contract_no} 合同的 V{sheet.confirm_version_no} 版本生成
    </div>
</body>
</html>"""
    if not HAS_WEASYPRINT:
        raise RuntimeError("WeasyPrint not installed. Run: pip install weasyprint")
    return HTML(string=html).write_pdf()
