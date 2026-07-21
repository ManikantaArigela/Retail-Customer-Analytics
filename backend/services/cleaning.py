import pandas as pd
import numpy as np

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes, cleans, and deduplicates the given Pandas DataFrame.
    """
    # 1. Deduplication
    initial_rows = len(df)
    df = df.drop_duplicates().copy()
    
    # 2. Trim string columns and convert column names to standard form for parsing
    df.columns = [str(col).strip() for col in df.columns]
    
    # 3. Handle missing values
    for col in df.columns:
        # Detect if column is numeric
        if pd.api.types.is_numeric_dtype(df[col]):
            # If numeric, fill missing values with mean (or 0 if all null)
            if df[col].isnull().all():
                df[col] = df[col].fillna(0)
            else:
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
        else:
            # If object/categorical/string
            # Convert to string and strip whitespace
            df[col] = df[col].astype(str).str.strip()
            # If all are 'nan' or empty, fill with 'Unknown'
            df[col] = df[col].replace({'nan': 'Unknown', '': 'Unknown', 'None': 'Unknown', 'NULL': 'Unknown'})
            # Mode imputation for missing categoricals
            non_empty = df[col][df[col] != 'Unknown']
            if not non_empty.empty:
                mode_val = non_empty.mode()[0]
                df[col] = df[col].replace({'Unknown': mode_val})
            else:
                df[col] = df[col].replace({'Unknown': 'Other'})
                
    # 4. Outlier Detection and Capping (for numeric columns except IDs)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        # Skip potential ID columns
        if 'id' in col.lower() or 'zip' in col.lower() or 'code' in col.lower():
            continue
            
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            # Cap outliers instead of dropping to preserve data completeness
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
            
    return df
