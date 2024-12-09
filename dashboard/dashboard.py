import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import requests
import csv
import random
import io
import plotly.express as px

# Fetch the CSV from the API
def fetch_and_preprocess_csv():
    # API details
    api_url = "https://ds-de-project.vercel.app/papers/csv"
    headers = {"X-API-Key": "a8c22b2d-21c7-4a8d-8a26-bd5f3e5e6d21"}

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        csv_content = response.text
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        # Prepare the DataFrame
        rows = []
        for row in csv_reader:
            rows.append({
                "title": row["title"],
                "citations": int(row.get("citations", 0)),  # Default to 0 if not found
                "documents": int(row.get("documents", 0)),  # Add a random number between 100-400
            })
        return pd.DataFrame(rows)
    else:
        st.error(f"Failed to fetch data from API. Status code: {response.status_code}")
        return None

# Streamlit app
st.title("K-Means Clustering on API Data")

# Check if data is already in session state
if "df" not in st.session_state:
    st.session_state.df = None

# Sidebar for fetching data
st.sidebar.subheader("Data Fetching")
if st.sidebar.button("Fetch Data from API"):
    st.session_state.df = fetch_and_preprocess_csv()

# Proceed if data is available
if st.session_state.df is not None:
    df = st.session_state.df

    # Display the DataFrame
    st.subheader("Fetched Data")
    st.write(df)

    # Sidebar for selecting k value
    st.sidebar.subheader("K-Means Parameters")
    k = st.sidebar.slider("Number of Clusters (k)", min_value=2, max_value=10, value=3)

    # Preprocess the data for clustering
    data = df[["citations", "documents"]]


    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)

    scaled_df = pd.DataFrame(scaled_data, columns=["citations", "documents"])

    # Perform K-Means clustering
    kmeans = KMeans(n_clusters=k, random_state=42)
    df["cluster"] = kmeans.fit_predict(scaled_data)

    # Display clustering results
    st.subheader("Clustering Results")
    st.write(df)

    # Plot the clusters using Plotly
    fig = px.scatter(
        df,
        x="citations",
        y="documents",
        color="cluster",
        hover_data=["title"],
        title="K-Means Clustering",
        labels={"citations": "Citations", "documents": "Documents"},
        color_continuous_scale=px.colors.sequential.Viridis   # Enhanced color palette
    )
    fig.update_traces(marker=dict(size=10, line=dict(width=2, color="DarkSlateGrey")))
    st.plotly_chart(fig, use_container_width=True)


    inertia = []
    k_range = range(1, k + 1)
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(scaled_data)
        inertia.append(kmeans.inertia_)

    # Plot the Elbow Method results using Plotly
    fig_elbow = px.line(x=list(k_range), y=inertia, markers=True,
                        title='Elbow Method for Determining Optimal k',
                        labels={'x': 'Number of clusters (k)', 'y': 'Inertia'})
    fig_elbow.update_layout(xaxis=dict(tickmode='linear'))
    st.plotly_chart(fig_elbow, use_container_width=True)
else:
    st.info("Click the button in the sidebar to fetch data from the API.")
