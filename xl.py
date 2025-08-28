import streamlit as st
import pandas as pd
import numpy as np
import io

class SmartWeightDistributor:
    def __init__(self):
        pass

    def find_weight_column(self, df):
        """Automatically find the column with weight data (numbers)"""
        weight_column = None
        max_numbers = 0
        
        for col in df.columns:
            numeric_count = pd.to_numeric(df[col], errors='coerce').notna().sum()
            if numeric_count > max_numbers:
                max_numbers = numeric_count
                weight_column = col
        return weight_column, max_numbers
    
    def shift_columns_and_create_containers(self, df, weight_column, user_defined_containers=5):
        """Shift columns to make room for containers and distribute weights"""
        weight_col_index = list(df.columns).index(weight_column)
        
        # If weight column is at the beginning, we need to shift everything
        if weight_col_index < user_defined_containers:
            # Calculate how many columns we need to shift
            shift_amount = user_defined_containers - weight_col_index
            
            # Create new column names for the shifted structure
            new_columns = {}
            
            # First, add container columns at the beginning
            for i in range(user_defined_containers):
                new_columns[f'Container_{i+1}'] = [0.0] * len(df)
            
            # Then add the original columns, shifted to the right
            for i, col in enumerate(df.columns):
                new_col_index = i + shift_amount
                new_columns[f'Column_{new_col_index}'] = df[col].values
            
            # Create new dataframe with shifted structure
            new_df = pd.DataFrame(new_columns)
            
            # Find the weight column in new structure
            weight_column_new = f'Column_{weight_col_index + shift_amount}'
            container_columns = [f'Container_{i+1}' for i in range(user_defined_containers)]
            
            return new_df, weight_column_new, container_columns
        else:
            # Normal case - weight column is after enough columns for containers
            container_columns = list(df.columns)[:weight_col_index]
            return df.copy(), weight_column, container_columns
    
    def distribute_weight(self, weight, num_containers):
        """Divide weight equally"""
        if pd.isna(weight) or weight <= 0:
            return [0] * num_containers
        weight_per_container = round(weight / num_containers, 2)
        return [weight_per_container] * num_containers
    
    def process_dataframe(self, df, user_defined_containers=5):
        """Process dataframe with smart column shifting"""
        # Find weight column first
        weight_column, weight_count = self.find_weight_column(df)
        if weight_column is None:
            st.error("❌ No numeric column found for weights!")
            return None
        
        st.info(f"🔍 Weight column detected: **{weight_column}** ({weight_count} numeric values)")
        
        # Shift columns and create containers if needed
        processed_df, final_weight_column, container_columns = self.shift_columns_and_create_containers(
            df, weight_column, user_defined_containers
        )
        
        st.info(f"📦 Container columns: {container_columns}")
        st.info(f"⚖️ Final weight column: {final_weight_column}")
        
        # Distribute weights
        processed_rows = 0
        for i, weight in enumerate(processed_df[final_weight_column]):
            if pd.notna(weight) and weight > 0:
                distribution = self.distribute_weight(weight, len(container_columns))
                for j, container_col in enumerate(container_columns):
                    processed_df.at[i, container_col] = distribution[j]
                processed_rows += 1
        
        st.success(f"✅ Processed {processed_rows} weights across {len(container_columns)} containers")
        
        return processed_df, final_weight_column, container_columns


# ----------------- STREAMLIT APP -----------------
st.set_page_config(page_title="Smart Weight Distributor", layout="wide")

st.title("🚀 Smart Weight Distribution System")
st.write("🤖 Upload a file and distribute weights automatically with smart column shifting.")

# Sidebar for configuration
st.sidebar.header("⚙️ Configuration")
user_defined_containers = st.sidebar.number_input(
    "📦 Number of containers:", 
    min_value=1, 
    value=5, 
    step=1,
    help="Specify how many containers to distribute weight across"
)

st.sidebar.markdown("""
### 🧠 How it works:
1. **Auto-detects** weight column (most numbers)
2. **Smart shifting**: If weight is in first columns, shifts everything to make room for containers
3. **Distributes** weight equally across containers
4. **Updates** your file automatically
""")

uploaded_file = st.file_uploader("📁 Upload your CSV or Excel file", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Read file
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file, header=None)
            st.info("📋 CSV file detected - reading without headers")
        else:
            df = pd.read_excel(uploaded_file)
            st.info("📊 Excel file detected")
        
        st.write(f"📏 File dimensions: **{len(df)} rows × {len(df.columns)} columns**")
        
        # Show original data
        st.write("### 📊 Original Data (first 10 rows)")
        st.dataframe(df.head(10), use_container_width=True)

        distributor = SmartWeightDistributor()
        
        # Preview weight column detection
        weight_column, weight_count = distributor.find_weight_column(df)
        
        if weight_column is not None:
            weight_col_index = list(df.columns).index(weight_column)
            
            # Show detection results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Weight Column", f"Column {weight_column}")
            with col2:
                st.metric("🔢 Numeric Values", weight_count)
            with col3:
                st.metric("📍 Column Position", weight_col_index + 1)
            
            # Show what will happen
            if weight_col_index < user_defined_containers:
                st.warning(f"⚠️ Weight column is at position {weight_col_index + 1}, but we need {user_defined_containers} containers. Columns will be shifted automatically.")
                st.info(f"🔄 Weight column will move from position {weight_col_index + 1} to position {user_defined_containers + (weight_col_index + 1)}")
            else:
                st.success(f"✅ Perfect! Weight column at position {weight_col_index + 1} with {weight_col_index} columns available for containers.")

            if st.button("🔄 Process File", type="primary"):
                with st.spinner("Processing file..."):
                    result = distributor.process_dataframe(df.copy(), user_defined_containers)
                
                if result:
                    processed_df, final_weight_col, container_cols = result

                    st.balloons()
                    st.success("🎉 File processed successfully!")
                    
                    # Show processing summary
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**📋 Processing Summary:**")
                        st.write(f"• Weight column: `{final_weight_col}`")
                        st.write(f"• Container columns: `{container_cols}`")
                        st.write(f"• Total rows processed: `{len(processed_df)}`")
                    
                    with col2:
                        # Show example calculations
                        sample_weights = processed_df[final_weight_col].dropna().head(3).tolist()
                        if sample_weights:
                            st.write("**📈 Example Calculations:**")
                            for weight in sample_weights:
                                if weight > 0:
                                    container_weight = round(weight / len(container_cols), 2)
                                    st.write(f"• Weight {weight} → {container_weight} each")

                    # Show processed data
                    st.write("### 📊 Processed Data (first 10 rows)")
                    st.dataframe(processed_df.head(10), use_container_width=True)
                    
                    # Show full data if requested
                    if st.checkbox("🔍 Show all processed data"):
                        st.dataframe(processed_df, use_container_width=True)

                    # Download option
                    file_ext = "csv" if uploaded_file.name.endswith(".csv") else "xlsx"
                    buffer = io.BytesIO()
                    
                    if file_ext == "csv":
                        processed_df.to_csv(buffer, index=False, header=False)
                        mime_type = "text/csv"
                    else:
                        processed_df.to_excel(buffer, index=False)
                        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    
                    buffer.seek(0)

                    st.download_button(
                        label="💾 Download Processed File",
                        data=buffer,
                        file_name=f"processed_{uploaded_file.name}",
                        mime=mime_type,
                        type="primary"
                    )
        else:
            st.error("❌ Could not detect a weight column! Make sure your file contains numeric data.")
            
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.write("Please make sure your file is a valid CSV or Excel file.")

else:
    # Instructions when no file is uploaded
    st.info("👆 Please upload a CSV or Excel file to get started.")
    
    st.write("### 📋 Instructions:")
    st.write("""
    1. **Upload** your CSV or Excel file
    2. **Configure** number of containers in the sidebar (default: 5)
    3. **Click Process** - the system will:
       - Auto-detect your weight column
       - Smart-shift columns if needed
       - Distribute weights equally across containers
       - Provide download link for processed file
    """)
    
    st.write("### 🎯 Example:")
    st.write("If your data has weights in the first column, the system will automatically shift everything to make room for container columns.")

# Footer
st.markdown("---")
st.markdown("🚀 **Smart Weight Distributor** - Automatically detects and distributes weights with intelligent column management.")