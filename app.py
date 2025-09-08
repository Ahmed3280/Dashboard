import pandas as pd
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.io as pio
import numpy as np

# --- Plotly dark theme ---
pio.templates.default = "plotly_dark"

# --- Colors ---
NO_SHOW_COLOR = '#FF9500'
SHOW_COLOR = '#007AFF'

# --- Load dataset ---
url = "https://raw.githubusercontent.com/Ahmed3280/Dashboard/refs/heads/main/KaggleV2-May-2016.csv"
df = pd.read_csv(url)

# --- Data cleaning ---
df = df[df['Age'] >= 0].copy()
df["ScheduledDay"] = pd.to_datetime(df["ScheduledDay"]).dt.tz_localize(None)
df["AppointmentDay"] = pd.to_datetime(df["AppointmentDay"]).dt.tz_localize(None)
df["WaitingDays"] = (df["AppointmentDay"] - df["ScheduledDay"]).dt.days
df["AppointmentDayOfWeek"] = df["AppointmentDay"].dt.day_name()
df['No-show'] = df['No-show'].replace({'No': 'No', 'Yes': 'Yes'})
df["No-show_flag"] = (df["No-show"] == "Yes").astype(int)
df['SMS_received_label'] = df['SMS_received'].astype(str)
df['Scholarship_label'] = df['Scholarship'].astype(str)
df['Hipertension_label'] = df['Hipertension'].astype(str)
df['Diabetes_label'] = df['Diabetes'].astype(str)
df['Alcoholism_label'] = df['Alcoholism'].astype(str)

# --- Prepare age group & day-of-week rates ---
df['Age_Group'] = pd.cut(df['Age'], bins=[0,10,20,30,40,50,60,70,80,90,100], right=False)
age_group_rate = df.groupby('Age_Group', observed=True)['No-show_flag'].mean().reset_index()
age_group_rate['No-show Rate (%)'] = age_group_rate['No-show_flag']*100
age_group_rate['Age_Group'] = age_group_rate['Age_Group'].astype(str)

day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_rate = df.groupby('AppointmentDayOfWeek', observed=True)['No-show_flag'].mean().reindex(day_order).reset_index()
day_rate['No-show Rate (%)'] = day_rate['No-show_flag']*100

# --- Initialize app ---
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# ================= Layout ================= #
app.layout = html.Div(style={'backgroundColor': '#1E1E1E', 'color': 'white'}, children=[
    dbc.Container([
        dbc.Row([dbc.Col(html.H1("📊 Medical Appointment Dashboard", className="text-center text-info mb-4"), width=12)]),

        # Overview cards
        dbc.Row([
            dbc.Col(dbc.Card([dbc.CardHeader("Total Appointments"), dbc.CardBody(html.H4(f"{df.shape[0]:,}"))], className="shadow text-center"), width=3),
            dbc.Col(dbc.Card([dbc.CardHeader("Average Age"), dbc.CardBody(html.H4(f"{df['Age'].mean():.1f}"))], className="shadow text-center"), width=3),
            dbc.Col(dbc.Card([dbc.CardHeader("Show Rate"), dbc.CardBody(html.H4(f"{100 - df['No-show'].value_counts(normalize=True)['Yes']*100:.1f}%"))], className="shadow text-center"), width=3),
            dbc.Col(dbc.Card([dbc.CardHeader("No-Show Rate"), dbc.CardBody(html.H4(f"{df['No-show'].value_counts(normalize=True)['Yes']*100:.1f}%"))], className="shadow text-center"), width=3),
        ], className="mb-4"),

        # Feature selection
        dbc.Row([dbc.Col([
            html.Label("Select Feature to Compare with Attendance:", className="font-weight-bold"),
            dcc.Dropdown(
                id="feature-dropdown",
                options=[
                    {"label": "Age", "value": "Age"},
                    {"label": "Gender", "value": "Gender"},
                    {"label": "Scholarship", "value": "Scholarship"},
                    {"label": "Hypertension", "value": "Hipertension"},
                    {"label": "Diabetes", "value": "Diabetes"},
                    {"label": "Alcoholism", "value": "Alcoholism"},
                    {"label": "SMS Received", "value": "SMS_received"},
                    {"label": "Waiting Days", "value": "WaitingDays"}
                ],
                value="Age",
                clearable=False
            )
        ], width={"size": 4, "offset": 4})], className="mb-4"),

        # Main graphs
        dbc.Row([dbc.Col(dcc.Graph(id="main-graph"), width=7), dbc.Col(dcc.Graph(id="target-distribution"), width=5)], className="mb-4"),
        dbc.Row([dbc.Col(dcc.Graph(id="gender-impact-graph"), width=6), dbc.Col(dcc.Graph(id="sms-impact-graph"), width=6)], className="mb-4"),
        dbc.Row([dbc.Col(dcc.Graph(id="waitingdays-by-day"), width=12)], className="mb-4"),

        # Additional insights
        dbc.Row([dbc.Col(html.H3("Additional Insights", className="text-center text-info mt-5 mb-3"), width=12)]),
        dbc.Row([dbc.Col(dcc.Graph(id="age-group-rate-graph"), width=6), dbc.Col(dcc.Graph(id="day-of-week-rate-graph"), width=6)], className="mb-4"),
    ], fluid=True)
])

# ================= Callbacks ================= #
@app.callback(Output("main-graph", "figure"), Input("feature-dropdown", "value"))
def update_main_graph(feature):
    if feature in ["Age", "WaitingDays"]:
        fig = px.histogram(df, x=feature, color="No-show", nbins=50,
                           color_discrete_map={"Yes": NO_SHOW_COLOR, "No": SHOW_COLOR},
                           title=f"Distribution of {feature} by Attendance")
    else:
        fig = px.histogram(df, x=feature, color="No-show", barmode="group",
                           color_discrete_map={"Yes": NO_SHOW_COLOR, "No": SHOW_COLOR},
                           title=f"Attendance by {feature}")
    fig.update_layout(title_font_color='white', title_font_size=24, font_color='white',
                      plot_bgcolor='#2c3e50', paper_bgcolor='#1E1E1E')
    fig.update_xaxes(title_font_color='white', title_font_size=18, showgrid=True)
    fig.update_yaxes(title_font_color='white', title_font_size=18, showgrid=True)
    return fig

@app.callback(Output("target-distribution", "figure"), Input("feature-dropdown", "value"))
def update_target_graph(_):
    fig = px.pie(df, names="No-show", color="No-show",
                 color_discrete_map={"Yes": NO_SHOW_COLOR, "No": SHOW_COLOR},
                 title="Show vs No-Show Distribution")
    fig.update_layout(title_font_color='white', title_font_size=24, font_color='white',
                      plot_bgcolor='#2c3e50', paper_bgcolor='#1E1E1E')
    return fig

@app.callback(Output("gender-impact-graph", "figure"), Input("feature-dropdown", "value"))
def update_gender_graph(_):
    gender_counts = df.groupby(["Gender", "No-show_flag"], observed=True).size().reset_index(name="count")
    fig = px.bar(gender_counts, x="Gender", y="count", color="No-show_flag", barmode="group",
                 color_discrete_map={1: NO_SHOW_COLOR, 0: SHOW_COLOR},
                 title="Attendance by Gender (0=Show, 1=No-show)")
    fig.update_layout(title_font_color='white', title_font_size=24, font_color='white',
                      plot_bgcolor='#2c3e50', paper_bgcolor='#1E1E1E')
    return fig

@app.callback(Output("sms-impact-graph", "figure"), Input("feature-dropdown", "value"))
def update_sms_graph(_):
    sms_counts = df.groupby(["SMS_received_label", "No-show_flag"], observed=True).size().reset_index(name="count")
    fig = px.bar(sms_counts, x="SMS_received_label", y="count", color="No-show_flag", barmode="group",
                 color_discrete_map={1: NO_SHOW_COLOR, 0: SHOW_COLOR},
                 title="Attendance by SMS Received (0=Show, 1=No-show)")
    fig.update_layout(title_font_color='white', title_font_size=24, font_color='white',
                      plot_bgcolor='#2c3e50', paper_bgcolor='#1E1E1E')
    return fig

@app.callback(Output("waitingdays-by-day", "figure"), Input("feature-dropdown", "value"))
def update_waiting_by_day(_):
    fig = px.box(df, x="AppointmentDayOfWeek", y="WaitingDays", color="No-show",
                 color_discrete_map={"Yes": NO_SHOW_COLOR, "No": SHOW_COLOR},
                 title="Waiting Days by Appointment Day of the Week")
    fig.update_layout(title_font_color='white', title_font_size=24, font_color='white',
                      plot_bgcolor='#2c3e50', paper_bgcolor='#1E1E1E')
    return fig

@app.callback(Output("age-group-rate-graph", "figure"), Input("feature-dropdown", "value"))
def update_age_rate_graph(_):
    fig = px.bar(age_group_rate, x='Age_Group', y='No-show Rate (%)', color_discrete_sequence=[NO_SHOW_COLOR],
                 title="No-Show Rate by Age Group")
    fig.update_layout(title_font_color='white', title_font_size=24, font_color='white',
                      plot_bgcolor='#2c3e50', paper_bgcolor='#1E1E1E')
    return fig

@app.callback(Output("day-of-week-rate-graph", "figure"), Input("feature-dropdown", "value"))
def update_day_rate_graph(_):
    fig = px.bar(day_rate, x='AppointmentDayOfWeek', y='No-show Rate (%)',
                 color_discrete_sequence=[NO_SHOW_COLOR],
                 title="No-Show Rate by Day of the Week")
    fig.update_layout(title_font_color='white', title_font_size=24, font_color='white',
                      plot_bgcolor='#2c3e50', paper_bgcolor='#1E1E1E')
    return fig

if __name__ == "__main__":
    app.run(debug=True)
