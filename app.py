import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

st.set_page_config(page_title="Goodfire Invoice Generator", page_icon="📄", layout="wide")

st.title("📄 Goodfire Invoice Generator")
st.markdown("Generate professional invoices from Close.com lead exports for MLS listings")

# Function to generate invoice PDF
def generate_invoice_pdf(filtered_df, billing_month, billing_year, company_name, price_per_listing):
    """Generate a PDF invoice from filtered lead data"""
    buffer = BytesIO()
    
    # Use landscape orientation for more horizontal space
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter),
                            topMargin=0.75*inch, bottomMargin=0.75*inch,
                            leftMargin=0.75*inch, rightMargin=0.75*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.black,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Create title
    month_name = datetime(billing_year, billing_month, 1).strftime('%B').upper()
    title = Paragraph(f"GOODFIRE REALTY LISTINGS - {month_name} BILLING", title_style)
    story.append(title)
    story.append(Spacer(1, 0.3*inch))
    
    # Prepare table data
    table_data = [['Date', 'MLS', 'Property', company_name]]
    
    for _, row in filtered_df.iterrows():
        # Extract relevant data
        date_listed = row.get('custom.Asset_MLS_Listing_Date', '')
        if pd.notna(date_listed):
            # Format date to M/D/YYYY
            try:
                date_obj = pd.to_datetime(date_listed)
                date_str = date_obj.strftime('%-m/%-d/%Y')  # Unix format for no leading zeros
            except:
                date_str = str(date_listed).split()[0] if date_listed else ''
        else:
            date_str = ''
        
        mls_number = str(row.get('custom.Asset_MLS#', '')) if pd.notna(row.get('custom.Asset_MLS#')) else ''
        
        # Build property description
        property_parts = []
        state = row.get('custom.All_State', '')
        county = row.get('custom.All_County', '')
        
        # Extract property name from display_name
        display_name = row.get('display_name', '')
        # Try to extract the base name before APN
        if 'APN' in display_name:
            base_name = display_name.split('APN')[0].strip()
        else:
            base_name = display_name
        
        if pd.notna(state) and state:
            property_parts.append(str(state))
        if pd.notna(county) and county:
            property_parts.append(str(county))
        if base_name:
            property_parts.append(base_name)
        
        # Add APN
        apn = row.get('custom.All_APN', '')
        if pd.notna(apn) and apn:
            property_parts.append(f"APN# {apn}")
        
        property_desc = ' '.join(property_parts)
        
        price = f"${price_per_listing:.2f}"
        
        table_data.append([date_str, mls_number, property_desc, price])
    
    # Calculate total
    total_amount = len(filtered_df) * price_per_listing
    
    # Create table with adjusted column widths for landscape orientation
    # Landscape letter is 11" x 8.5", minus margins = ~9.5" width available
    # Giving more space to Property column
    col_widths = [1.0*inch, 1.2*inch, 6.0*inch, 1.3*inch]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    
    # Style the table
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Data rows
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Price column right-aligned
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.5*inch))
    
    # Total section - adjusted for landscape width
    total_data = [
        ['Total', f'${total_amount:.2f}'],
        ['Billing Date', datetime.now().strftime('%-m/%-d/%Y')]
    ]
    
    total_table = Table(total_data, colWidths=[8.2*inch, 1.3*inch])
    total_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEABOVE', (0, 0), (-1, 0), 1.5, colors.black),
    ]))
    
    story.append(total_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# File upload
uploaded_file = st.file_uploader("Upload Close.com CSV Export", type=['csv'])

if uploaded_file is not None:
    try:
        # Read the CSV
        df = pd.read_csv(uploaded_file)
        
        st.success(f"✅ Loaded {len(df)} leads successfully!")
        
        # Configuration section
        st.subheader("📋 Invoice Configuration")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company_name = st.text_input("Company Name", value="RLV22 LLC", 
                                        help="Name of the company being billed")
        
        with col2:
            price_per_listing = st.number_input("Price per Listing", 
                                               min_value=0.0, 
                                               value=200.0, 
                                               step=10.0,
                                               help="Dollar amount charged per MLS listing")
        
        with col3:
            billing_month = st.selectbox("Billing Month", 
                                        options=list(range(1, 13)),
                                        format_func=lambda x: datetime(2025, x, 1).strftime('%B'),
                                        index=datetime.now().month - 1)
        
        billing_year = st.number_input("Billing Year", 
                                       min_value=2020, 
                                       max_value=2030, 
                                       value=datetime.now().year,
                                       step=1)
        
        st.divider()
        
        # Filtering section
        st.subheader("🔍 Filter Criteria")
        
        # Check for MLS-related columns
        has_mls = 'custom.Asset_MLS#' in df.columns
        has_listing_date = 'custom.Asset_MLS_Listing_Date' in df.columns
        has_status = 'primary_opportunity_status_label' in df.columns
        
        if not has_mls or not has_listing_date:
            st.warning("⚠️ Warning: Required columns not found in CSV. Please ensure your export includes 'custom.Asset_MLS#' and 'custom.Asset_MLS_Listing_Date'")
        
        # Filter options
        col1, col2 = st.columns(2)
        
        with col1:
            filter_by_status = st.checkbox("Filter by Status", value=True)
            if filter_by_status and has_status:
                status_filter = st.selectbox("Status", 
                                            options=['Listed', 'Under Contract', 'Purchased'],
                                            index=0)
        
        with col2:
            filter_by_date = st.checkbox("Filter by Listing Date", value=True)
        
        filter_mls_only = st.checkbox("Include only leads with MLS numbers", value=True)
        
        # Apply filters
        filtered_df = df.copy()
        
        # Filter by status
        if filter_by_status and has_status:
            filtered_df = filtered_df[filtered_df['primary_opportunity_status_label'] == status_filter]
            st.info(f"Filtered to {len(filtered_df)} leads with status: {status_filter}")
        
        # Filter by listing date
        if filter_by_date and has_listing_date:
            # Convert listing date to datetime
            filtered_df['listing_date_dt'] = pd.to_datetime(filtered_df['custom.Asset_MLS_Listing_Date'], errors='coerce')
            
            # Filter for the selected billing month/year
            mask = (filtered_df['listing_date_dt'].dt.month == billing_month) & \
                   (filtered_df['listing_date_dt'].dt.year == billing_year)
            filtered_df = filtered_df[mask]
            st.info(f"Filtered to {len(filtered_df)} leads listed in {datetime(billing_year, billing_month, 1).strftime('%B %Y')}")
        
        # Filter by MLS number existence
        if filter_mls_only and has_mls:
            filtered_df = filtered_df[filtered_df['custom.Asset_MLS#'].notna() & (filtered_df['custom.Asset_MLS#'] != '')]
            st.info(f"Filtered to {len(filtered_df)} leads with MLS numbers")
        
        if len(filtered_df) == 0:
            st.warning("⚠️ No leads match the current filter criteria. Please adjust your filters.")
        else:
            st.divider()
            
            # Preview section
            st.subheader("📊 Invoice Preview")
            
            # Display summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Listings", len(filtered_df))
            with col2:
                total_amount = len(filtered_df) * price_per_listing
                st.metric("Total Amount", f"${total_amount:,.2f}")
            with col3:
                month_name = datetime(billing_year, billing_month, 1).strftime('%B %Y')
                st.metric("Billing Period", month_name)
            
            # Show preview of data
            preview_df = filtered_df[['display_name', 'custom.Asset_MLS#', 'custom.Asset_MLS_Listing_Date', 
                                     'custom.All_State', 'custom.All_County', 'custom.All_APN']].copy()
            preview_df.columns = ['Property Name', 'MLS#', 'Listing Date', 'State', 'County', 'APN']
            
            st.dataframe(preview_df, use_container_width=True)
            
            st.divider()
            
            # Generate invoice button
            if st.button("📄 Generate Invoice PDF", type="primary"):
                with st.spinner("Generating invoice..."):
                    pdf_buffer = generate_invoice_pdf(filtered_df, billing_month, billing_year, 
                                                     company_name, price_per_listing)
                    
                    # Create filename
                    filename = f"{billing_year}-{billing_month:02d}-{datetime.now().day:02d}_Goodfire_Realty_Billing.pdf"
                    
                    st.success("✅ Invoice generated successfully!")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Invoice PDF",
                        data=pdf_buffer,
                        file_name=filename,
                        mime="application/pdf"
                    )
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.write("Please make sure you've uploaded a valid Close.com CSV export.")
        with st.expander("See error details"):
            st.code(str(e))

else:
    st.info("👆 Please upload your Close.com CSV export to begin")
    
    st.markdown("""
    ### 📖 How to Use
    
    1. **Export from Close.com**: Export the listings using the 📊 Goodfire Monthly Billing smartview. Export all fields.
    2. **Upload CSV**: Use the file uploader above
    3. **Configure**: Set company name, pricing, and billing period
    4. **Filter**: Select which leads to include in the invoice
    5. **Generate**: Click to create your PDF invoice
    
    ⚠️ **NOTE:** The "📊 Goodfire Monthly Billing" smartview in Close.com is set for "This Month" and intended to be run prior to the end of the current month. If this billing is generated at the beginning of the new month, you'll need to temporarily change the period in Close.com to "Last Month".
    
    ### 📋 Required CSV Columns
    
    The following columns should be in your Close.com export:
    - `custom.Asset_MLS#` - MLS listing number
    - `custom.Asset_MLS_Listing_Date` - Date the property was listed
    - `custom.All_State` - Property state
    - `custom.All_County` - Property county
    - `custom.All_APN` - Property APN number
    - `display_name` - Property display name
    - `primary_opportunity_status_label` - Lead status
    
    ### 💡 Tips
    
    - Filter by listing date to generate monthly invoices automatically
    - Use status filters to include only active listings
    - The invoice format matches your standard Goodfire Realty billing format
    - Landscape orientation provides more space for property names
    """)
