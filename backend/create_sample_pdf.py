"""
Create sample PDF for RAG demo - Warehouse SOP
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

def create_warehouse_sop_pdf():
    """Create a sample warehouse SOP PDF for RAG demo."""
    
    doc = SimpleDocTemplate(
        "sample_warehouse_sop.pdf",
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("SOP GUDANG INVENINSIGHT AI", styles['Heading1'])
    story.append(title)
    story.append(Spacer(1, 0.2*inch))
    
    # Subtitle
    subtitle = Paragraph("Standard Operating Procedure - Warehouse Management", styles['Heading2'])
    story.append(subtitle)
    story.append(Spacer(1, 0.2*inch))
    
    # Section 1: Penerimaan Barang
    section1 = Paragraph("1. PENERIMAAN BARANG", styles['Heading3'])
    story.append(section1)
    story.append(Spacer(1, 0.1*inch))
    
    text1 = Paragraph("""
    1.1 Verifikasi invoice dan packing list dari supplier.
    1.2 Cek kondisi fisik barang (tidak rusak, tidak cacat).
    1.3 Scan barcode dan input ke sistem inventory.
    1.4 Simpan barang di area penerimaan sementara.
    1.5 Konfirmasi penerimaan ke purchasing department.
    """, styles['Normal'])
    story.append(text1)
    story.append(Spacer(1, 0.2*inch))
    
    # Section 2: Penyimpanan Barang
    section2 = Paragraph("2. PENYIMPAN BARANG", styles['Heading3'])
    story.append(section2)
    story.append(Spacer(1, 0.1*inch))
    
    text2 = Paragraph("""
    2.1 Kategorikan barang berdasarkan jenis (Elektronik, ATK, dll).
    2.2 Simpan di rak yang sesuai dengan kategori.
    2.3 Gunakan FIFO (First In First Out) untuk perishable items.
    2.4 Update lokasi rak di sistem inventory.
    2.5 Pastikan rak tidak melebihi kapasitas maksimal.
    """, styles['Normal'])
    story.append(text2)
    story.append(Spacer(1, 0.2*inch))
    
    # Section 3: Retur Barang Rusak
    section3 = Paragraph("3. RETUR BARANG RUSAK", styles['Heading3'])
    story.append(section3)
    story.append(Spacer(1, 0.1*inch))
    
    text3 = Paragraph("""
    3.1 Barang rusak harus dilaporkan dalam 24 jam.
    3.2 Isi form retur (Form R-05) dengan detail kerusakan.
    3.3 Foto bukti kerusakan harus dilampirkan.
    3.4 Kirim ke quality control untuk verifikasi.
    3.5 Batas waktu retur ke supplier: 7 hari dari tanggal penerimaan.
    3.6 Barang di karantina area hingga proses retur selesai.
    """, styles['Normal'])
    story.append(text3)
    story.append(Spacer(1, 0.2*inch))
    
    # Section 4: Minimum Stock Policy
    section4 = Paragraph("4. MINIMUM STOCK POLICY", styles['Heading3'])
    story.append(section4)
    story.append(Spacer(1, 0.1*inch))
    
    # Table for minimum stock
    table_data = [
        ['Kategori', 'Minimum Stock', 'Lead Time'],
        ['Elektronik', '10 unit', '3 hari'],
        ['ATK', '20 unit', '2 hari'],
        ['Perabotan', '5 unit', '7 hari'],
        ['Komponen', '50 unit', '5 hari'],
    ]
    
    table = Table(table_data, colWidths=[2*inch, 2*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.2*inch))
    
    text4 = Paragraph("""
    Note: Stok di bawah minimum akan trigger auto-reorder ke purchasing.
    """, styles['Normal'])
    story.append(text4)
    story.append(Spacer(1, 0.2*inch))
    
    # Section 5: Safety Protocol
    section5 = Paragraph("5. SAFETY PROTOCOL", styles['Heading3'])
    story.append(section5)
    story.append(Spacer(1, 0.1*inch))
    
    text5 = Paragraph("""
    5.1 Gunakan APD (Alat Pelindung Diri) saat bekerja.
    5.2 Forklift hanya boleh dioperasikan oleh operator bersertifikat.
    5.3 Larangan merokok di area gudang.
    5.4 Barang berat di atas 25kg harus menggunakan alat bantu.
    5.5 Emergency exit harus selalu clear dan accessible.
    """, styles['Normal'])
    story.append(text5)
    story.append(Spacer(1, 0.2*inch))
    
    # Section 6: Shift Handover
    section6 = Paragraph("6. SHIFT HANDOVER", styles['Heading3'])
    story.append(section6)
    story.append(Spacer(1, 0.1*inch))
    
    text6 = Paragraph("""
    6.1 Supervisor shift pagi (08:00-16:00) wajib lapor ke shift sore.
    6.2 Update status barang yang sedang dalam proses.
    6.3 Catat kejadian penting di logbook digital.
    6.4 Cek kunci dan security sebelum pulang.
    6.5 Pastikan area bersih dan rapi sebelum handover.
    """, styles['Normal'])
    story.append(text6)
    story.append(Spacer(1, 0.2*inch))
    
    # Footer
    footer = Paragraph("Dokumen ini bersifat confidential. Hanya untuk internal use.", styles['Normal'])
    story.append(footer)
    
    doc.build(story)
    print("Sample SOP PDF created successfully: sample_warehouse_sop.pdf")

if __name__ == "__main__":
    create_warehouse_sop_pdf()
