import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

file_path = r"C:\Users\aubre\Downloads\Datasets\world-data-2023.csv"

data = pd.read_csv(file_path)



# Display the first few rows of the dataset
print(data.head())

# Get a summary of the dataset
print(data.info())

# Check for missing values
print(data.isnull().sum())

for col in data.columns:
    pct_missing = np.mean(data[col].isnull())
    print('{} - {}%'.format(col, pct_missing))
# Get basic statistics of the dataset
print(data.describe())

# Data cleaning
data.dtypes

data = data.dropna()

# Fill missing values
data['column_name'] = data['column_name'].fillna(data['column_name'].mean())

# Remove duplicates
data = data.drop_duplicates()



# Vis and Correlation

#Add Columns

# CO2_Emissions_Per_Capita
num_data['CO2_Emissions_Per_Capita'] = num_data['Co2-Emissions'] / num_data['Population']
print(num_data[['Co2-Emissions', 'Population', 'CO2_Emissions_Per_Capita']])

# Converting formats and grabbing numerical columns
num_data = data[[
    'Country','Density\n(P/Km2)', 'Agricultural Land100( %)', 'Land Area(Km2)',
    'Armed Forces size', 'Birth Rate', 'Co2-Emissions',
    'CPI', 'Fertility Rate', 'Forested Area100(%)',
    'Gasoline Price', 'GDP', 'Gross primary education enrollment (%)',
    'Gross tertiary education enrollment (%)', 'Infant mortality', 'Life expectancy',
    'Maternal mortality ratio', 'Minimum wage', 'Out of pocket health expenditure100',
    'Physicians per thousand', 'Population', 'Population: Labor force participation100(%)',
    'Tax revenue100(%)', 'Total tax rate', 'Unemployment rate100',
    'Urban_population']]

print(num_data)

columns_to_convert = [
    'Density\n(P/Km2)', 'Agricultural Land100( %)', 'Land Area(Km2)',
    'Armed Forces size', 'Birth Rate', 'Co2-Emissions', 'CPI',
    'Fertility Rate', 'Forested Area100(%)', 'Gasoline Price', 'GDP',
    'Gross primary education enrollment (%)',
    'Gross tertiary education enrollment (%)', 'Infant mortality',
    'Life expectancy', 'Maternal mortality ratio', 'Minimum wage',
    'Out of pocket health expenditure100', 'Physicians per thousand',
    'Population', 'Population: Labor force participation100(%)',
    'Tax revenue100(%)', 'Total tax rate', 'Unemployment rate100',
    'Urban_population'
]


# Loop through the columns and apply the conversion
# Quick Clean
for column in columns_to_convert:
    # Convert to numeric, coerce errors to NaN
    num_data[column] = pd.to_numeric(num_data[column], errors='coerce')
    
    # Fill NaN with the mean of the column
    mean_value = num_data[column].mean()
    num_data[column] = num_data[column].fillna(mean_value)
    
    # Convert the column to integers
    num_data[column] = num_data[column].astype(int)


# Correlation Heatmap
plt.style.use('dark_background')
plt.figure(figsize=(18, 12))
correlation_matrix = num_data.drop(columns=['Country','CO2_Emissions_Per_Capita']).corr(method='pearson')
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
plt.xticks(rotation=90)
plt.title('Correlation of Numerical Values')
plt.show()


#Histogram of CO2 Emissions
plt.style.use('dark_background')
num_data['Co2-Emissions'] = pd.to_numeric(num_data['Co2-Emissions'], errors='coerce')
sorted_data = num_data.sort_values(by='Co2-Emissions', ascending=False)
plt.bar(x=sorted_data['Country'], height=sorted_data['Co2-Emissions'])
plt.xticks(rotation=90)
plt.xlabel('Country')
plt.ylabel('CO2 Emissions')
plt.title('CO2 Emissions by Country (Sorted)')
plt.show()

#Histogram of CO2 Emissions Per Capita
plt.style.use('dark_background')
num_data['CO2_Emissions_Per_Capita'] = pd.to_numeric(num_data['CO2_Emissions_Per_Capita'], errors='coerce')
sorted_data = num_data.sort_values(by='CO2_Emissions_Per_Capita', ascending=False)
plt.bar(x=sorted_data['Country'], height=sorted_data['CO2_Emissions_Per_Capita'])
plt.xticks(rotation=90)
plt.xlabel('Country')
plt.ylabel('CO2 Emissions Per Capita', fontsize=20)
plt.title('CO2 Emissions Per Capita by Country (Sorted)')
plt.show()

#Histogram of CO2 Emissions of Specified Counties
plt.style.use('dark_background')
selected_countries = ['United States', 'China', 'India', 'Germany', 'Russia']
filtered_data = num_data[num_data['Country'].isin(selected_countries)]
sorted_data = filtered_data.sort_values(by='Co2-Emissions', ascending=False)
plt.bar(x=sorted_data['Country'], height=sorted_data['Co2-Emissions'])
plt.xticks(rotation=90)
plt.xlabel('')
plt.ylabel('CO2 Emissions',  fontsize=20)
plt.title('CO2 Emissions by Country (Sorted)')
plt.show()

#Histogram of CO2 Emissions Per Capita of Specified Counties
plt.style.use('dark_background')
selected_countries = ['United States', 'China', 'India', 'Germany', 'Russia']
filtered_data = num_data[num_data['Country'].isin(selected_countries)]
sorted_data = filtered_data.sort_values(by='CO2_Emissions_Per_Capita', ascending=False)
plt.bar(x=sorted_data['Country'], height=sorted_data['CO2_Emissions_Per_Capita'])
plt.xticks(rotation=90)
plt.xlabel('')
plt.ylabel('CO2 Emissions Per Capita',  fontsize=20)
plt.title('CO2 Emissions Per Capita by Country (Sorted)')
plt.show()

#Histogram of Physicians per thousand of Specified Counties
plt.style.use('dark_background')
selected_countries = ['United States', 'China', 'India', 'Germany', 'Russia']
filtered_data = num_data[num_data['Country'].isin(selected_countries)]
sorted_data = filtered_data.sort_values(by='Physicians per thousand', ascending=False)
plt.bar(x=sorted_data['Country'], height=sorted_data['Physicians per thousand'], )
plt.xticks(rotation=90)
plt.xlabel('Country')
plt.ylabel('Physicians per thousand')
plt.title('Physicians per thousand by Country (Sorted)')
plt.show()

#PieChart of CO2 Emissions of Specified Counties
selected_countries = ['United States', 'China', 'India', 'Germany', 'Russia']
filtered_data = num_data[num_data['Country'].isin(selected_countries)]
filtered_data = filtered_data.dropna()
plt.pie(filtered_data['Co2-Emissions'], labels=filtered_data['Country'], autopct='%1.1f%%')
plt.title('CO2 Emissions by Country')
plt.show()

#PieChart of CO2 Emissions Per Capita of Specified Counties
selected_countries = ['United States', 'China', 'India', 'Germany', 'Russia']
filtered_data = num_data[num_data['Country'].isin(selected_countries)]
filtered_data = filtered_data.dropna()
plt.pie(filtered_data['CO2_Emissions_Per_Capita'], labels=filtered_data['Country'], autopct='%1.1f%%')
plt.title('CO2 Emissions per Capita by Country')
plt.show()