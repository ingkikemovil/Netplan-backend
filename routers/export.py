from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

router = APIRouter()


class ExportEdge(BaseModel):
    source_name: str
    target_name: str
    cost: float
    conn_type: str


class ExportRequest(BaseModel):
    project_name: str
    algorithm: str
    total_cost: float
    nodes_connected: int
    edges_used: int
    tree_edges: List[ExportEdge]


@router.post("/pdf")
def export_pdf(payload: ExportRequest):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Netplan - Resultados MST", styles["Title"]))
    story.append(Paragraph(f"Proyecto: {payload.project_name}", styles["Heading2"]))
    story.append(Spacer(1, 12))

    info_data = [
        ["Algoritmo", payload.algorithm.upper()],
        ["Costo Total", f"${payload.total_cost:,.2f}"],
        ["Nodos Conectados", str(payload.nodes_connected)],
        ["Conexiones Usadas", str(payload.edges_used)],
    ]
    info_table = Table(info_data, colWidths=[200, 200])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Conexiones del Ãrbol Ã“ptimo", styles["Heading3"]))
    edge_data = [["Origen", "Destino", "Costo", "Tipo"]]
    for e in payload.tree_edges:
        edge_data.append([e.source_name, e.target_name, f"${e.cost:,.2f}", e.conn_type])

    edge_table = Table(edge_data, colWidths=[130, 130, 100, 100])
    edge_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(edge_table)

    doc.build(story)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Netplan_{payload.project_name}.pdf"'}
    )


@router.post("/excel")
def export_excel(payload: ExportRequest):
    buffer = io.BytesIO()
    wb = xlsxwriter.Workbook(buffer)

    ws = wb.add_worksheet("Resultados")
    bold = wb.add_format({"bold": True, "bg_color": "#2563eb", "font_color": "white"})
    normal = wb.add_format({"border": 1})
    money = wb.add_format({"num_format": "$#,##0.00", "border": 1})

    ws.write(0, 0, "Netplan - Ãrbol de ExpansiÃ³n MÃ­nima", wb.add_format({"bold": True, "font_size": 14}))
    ws.write(1, 0, f"Proyecto: {payload.project_name}")
    ws.write(2, 0, f"Algoritmo: {payload.algorithm.upper()}")
    ws.write(3, 0, f"Costo Total: ${payload.total_cost:,.2f}")
    ws.write(4, 0, f"Nodos conectados: {payload.nodes_connected}")

    row = 6
    for col, header in enumerate(["Origen", "Destino", "Costo", "Tipo"]):
        ws.write(row, col, header, bold)

    for e in payload.tree_edges:
        row += 1
        ws.write(row, 0, e.source_name, normal)
        ws.write(row, 1, e.target_name, normal)
        ws.write(row, 2, e.cost, money)
        ws.write(row, 3, e.conn_type, normal)

    ws.set_column(0, 3, 20)
    wb.close()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="Netplan_{payload.project_name}.xlsx"'}
    )
