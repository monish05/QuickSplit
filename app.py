import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode
import getBill  # Assuming getBill is a custom module
import os  # For file handling

# Sidebar with Logo and App Name
with st.sidebar:
    st.image("logo.png", use_column_width=True)  # Display the logo (ensure 'logo.png' is in the same directory)
    st.title("Quick Split App")
    st.write("Easily split your bills among participants:")
    st.write("- Equal split")
    st.write("- Unequal split")

# Main Content
st.title("Welcome to the Quick Split App")
st.write("""
With this app, you can:
- Split bills equally among participants.
- Split bills unequally by assigning quantities for each item to specific people.
Upload your bill image to get started!
""")

# Upload Image
uploaded_file = st.file_uploader("Upload your bill image (PNG, JPG, JPEG):", type=["png", "jpg", "jpeg"])

if uploaded_file is not None:
    # Save the uploaded image temporarily
    temp_file_path = os.path.join("temp", uploaded_file.name)
    os.makedirs("temp", exist_ok=True)  # Ensure temp directory exists
    with open(temp_file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())  # Save uploaded file to disk
    
    st.success(f"Bill image uploaded successfully and saved to {temp_file_path}!")

    # Load data using the saved file path
    try:
        extract_text = getBill.GetSplitDetails(temp_file_path)
        output = extract_text.get_price_and_quantity()  # Extracted data
        df = pd.DataFrame(output)  # Create DataFrame dynamically

        if df.empty:
            st.error("No valid data could be extracted from the uploaded image. Please try again.")
        else:
            # Proceed with the rest of the application logic
            st.subheader("Split Your Bill")
            st.write("Now, you can add participant names and choose how to split the bill.")

            # Get names dynamically
            st.subheader("Add Names for the Split")
            names_input = st.text_area(
                "Enter the names of the people, separated by commas (e.g., John, Sarah, Mike):"
            )
            names = [name.strip() for name in names_input.split(",") if name.strip()]  # Parse names

            if names:
                st.write(f"People included in the split: {', '.join(names)}")
                num_of_people = len(names)

                # Ask if split should be equal or unequal
                split_type = st.radio(
                    "Do you want to split the bill equally or unequally?",
                    ("Equal", "Unequal"),
                    index=1
                )

                if split_type == "Equal":
                    # Split equally
                    st.subheader("Equal Split Table")
                    # Add a column for deletion
                    df['Include'] = True  # Default to include all rows

                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_default_column(editable=True)
                    gb.configure_column("Include", editable=True)  # Make Include column editable
                    grid_options = gb.build()

                    # Display the grid
                    grid_response = AgGrid(
                        df,
                        gridOptions=grid_options,
                        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                        update_mode=GridUpdateMode.VALUE_CHANGED,
                        height=400,
                        fit_columns_on_grid_load=True,
                    )

                    # Get updated data
                    updated_df = grid_response["data"]

                    # Filter rows where 'Include' is True
                    filtered_df = updated_df[updated_df["Include"]]
                    filtered_df["Price_Per_Unit"] = filtered_df["Total_Price"] / num_of_people

                    # Display Total Cost Per Person in Sidebar
                    with st.sidebar:
                        st.header("Total Cost Per Person")
                        for name in names:
                            total = filtered_df["Price_Per_Unit"].sum()
                            st.write(f"{name} owes: ₹{total:.2f}")
                else:
                    # Add columns for each person dynamically for unequal split
                    for name in names:
                        df[name] = 0  # Initialize quantities to 0

                    # Configure AgGrid for editing
                    df['Include'] = True
                    gb = GridOptionsBuilder.from_dataframe(df)
                    gb.configure_default_column(editable=True)
                    gb.configure_column("Name", editable=False)  # Disable editing for 'Name'
                    gb.configure_column("Quantity", editable=True)  # Disable editing for 'Quantity'
                    gb.configure_column("Include", editable=True)
                    grid_options = gb.build()

                    # Display the grid
                    st.subheader("Assign Quantities Directly in the Table")
                    grid_response = AgGrid(
                        df,
                        gridOptions=grid_options,
                        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                        update_mode=GridUpdateMode.VALUE_CHANGED,
                        height=400,
                        fit_columns_on_grid_load=True,
                    )

                    # Get updated data
                    updated_filtered_df = grid_response["data"]
                    updated_filtered_df = updated_filtered_df[updated_filtered_df["Include"]]

                    # Validation Check
                    validation_passed = True
                    for index, row in updated_filtered_df.iterrows():
                        total_assigned = sum(row[name] for name in names)
                        if total_assigned > row["Quantity"] or ((row[names] != 0).all() and total_assigned != row["Quantity"]):
                            validation_passed = False
                            st.error(
                                f"Row {index + 1}: The total assigned quantities ({total_assigned}) "
                                f"do not match the available quantity'."
                            )

                    # Show Total Cost Per Person in Sidebar only if validation passes
                    if validation_passed:
                        add_to_split = updated_filtered_df.loc[(updated_filtered_df[names] == 0).all(axis=1), "Total_Price"].sum() / len(names)
                        with st.sidebar:
                            st.header("Total Cost Per Person")
                            updated_filtered_df["Price_Per_Unit"] = (
                                updated_filtered_df["Total_Price"] / updated_filtered_df["Quantity"]
                            )
                            for name in names:
                                total = updated_filtered_df[name] * updated_filtered_df["Price_Per_Unit"]
                                st.write(f"{name} owes: ${total.sum() + add_to_split:.2f}")
                    else:
                        st.warning("Please fix the errors above before proceeding to view the total costs.")
            else:
                st.warning("Please enter names to start splitting the bill.")       
            
    except Exception as e:
        st.error(f"An error occurred while processing the image: {e}")
else:
    st.info("Please upload a bill image to get started.")
