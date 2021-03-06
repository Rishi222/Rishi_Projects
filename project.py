# -*- coding: utf-8 -*-
"""
Created on Sun Nov  4 09:06:12 2018

@author: sivar
"""
#ATTRIBUTES USED
Item_Fat_Content 
Item_Identifier               
Item_MRP                      
Item_Outlet_Sales             
Item_Type                       
Item_Visibility              
Item_Weight                    
Outlet_Establishment_Year        
Outlet_Identifier               
Outlet_Location_Type             
Outlet_Size                      
Outlet_Type 

import pandas as pd
import numpy as np

train= pd.read_csv('train_big.csv')
test= pd.read_csv('test_big.csv')

#NOW WE JOIN THE TEST AND TRAIN MODELS WITH A COLUMN CALLES AS SOURCE SPECIFYING WHERE IT CAME FROM
train['source']='train'
test['source']='test'
data=pd.concat([train,test],ignore_index=True)
print (train.shape, test.shape, data.shape)      
#OUTPUT (8523, 13) (5681, 12) (14204, 13)

#missing values
data.apply(lambda x: sum(x.isnull()))
#OUTPUT
Item_Fat_Content                0
Item_Identifier                 0
Item_MRP                        0
Item_Outlet_Sales            5681
Item_Type                       0
Item_Visibility                 0
Item_Weight                  2439
Outlet_Establishment_Year       0
Outlet_Identifier               0
Outlet_Location_Type            0
Outlet_Size                  4016
Outlet_Type                     0
source                          0

#item outlet sales can have zero values as it means there was no sales

data.describe()


#unique values
data.apply(lambda x: len(x.unique()))
#OUTPUT
Item_Fat_Content                 5
Item_Identifier               1559
Item_MRP                      8052
Item_Outlet_Sales             3494
Item_Type                       16
Item_Visibility              13006
Item_Weight                    416
Outlet_Establishment_Year        9
Outlet_Identifier               10
Outlet_Location_Type             3
Outlet_Size                      4
Outlet_Type                      4
source                           2

#finding the frequency of different categories in each nominal data
cat_col=[x for x in data.dtypes.index if data.dtypes[x]=='object']
#exlude two columns
cat_col=[x for x in cat_col if x not in ['Item_Identifier','Outlet_Identifier','source']]
#print frequency
for col in cat_col:
    print ('\nFrequency of category for varieble %s'%col)
    print (data[col].value_counts())
#OUTPUT
Frequency of category for varieble Item_Fat_Content
Low Fat    8485
Regular    4824
LF          522
reg         195
low fat     178
Name: Item_Fat_Content, dtype: int64
#from Item_Fat_Content we can see the low fat is repeated twice as lf and Low Fat similarly other items

#DATA CLEANING

median_v=data['Item_Weight'].median()      
data['Item_Weight']=data['Item_Weight'].fillna(median_v)

sum(data['Item_Weight'].isnull())

#as it is categorical we replace it with mode value
mode_v=data['Outlet_Size'].mode()      
data['Outlet_Size']=data['Outlet_Size'].fillna('Medium')

sum(data['Outlet_Size'].isnull())
       
#in Item_Visibility column there are lot of zero values which makes no sense, so lets consider it as missing value and replace it with the mean
mean_item=data['Item_Visibility'].mean(skipna=True)
data['Item_Visibility']=data.Item_Visibility.mask(data.Item_Visibility==0, mean_item)

sum(data['Item_Visibility']==0)

# Consider combining Outlet_Type
data.pivot_table(values='Item_Outlet_Sales',index='Outlet_Type')
#OUTPUT
                   Item_Outlet_Sales
Outlet_Type                         
Grocery Store             339.828500
Supermarket Type1        2316.181148
Supermarket Type2        1995.498739
Supermarket Type3        3694.038558
#there is significant difference between each store

#creating a new feature which has Item_Visibility for each product(product id is given in Item_Identifier) thus in future using this column we can compare visibility given to each product in different stores
#Determine average visibility of a product
visibility_avg = data.pivot_table(values='Item_Visibility', index='Item_Identifier')

#now in order to find the mean visibility of produts in all store do the following
#Determine another variable with means ratio
data['Item_Visibility_MeanRatio'] = data.apply(lambda x: x['Item_Visibility']/visibility_avg[x['Item_Visibility']], axis=1)
print (data['Item_Visibility_MeanRatio'].describe())


#there are 16 item_type thus we can combine them with the tree types of Item_Identifier of first two letters
#Get the first two characters of ID:
data['Item_Type_Combined'] = data['Item_Identifier'].apply(lambda x: x[0:2])
#Rename them to more intuitive categories:
data['Item_Type_Combined'] = data['Item_Type_Combined'].map({'FD':'Food',
                                                             'NC':'Non-Consumable',
                                                             'DR':'Drinks'})
data['Item_Type_Combined'].value_counts() 
#OUTPUT
Food              10201
Non-Consumable     2686
Drinks             1317
Name: Item_Type_Combined, dtype: int64
#from output food has the highest sales

#we can use the Item_Type_Combined column to find the average of sales of the 3 product types
data.pivot_table(values='Item_Outlet_Sales', index='Item_Type_Combined') #thus food has the highest sales average

#We wanted to make a new column depicting the years of operation of a store
#for this we can make use of Outlet_Establishment_Year 
data['Outlet_Years'] = 2013 - data['Outlet_Establishment_Year']  #2013 is used because problem statement tells data was taken upto 2013
data['Outlet_Years'].describe() #thus stores have 4-28 years of operation


#from Item_Fat_Content we saw that low fat is repeated twice as lf and Low Fat similarly other items
#this typo error can be overcome by following method
#coding the before and after changes
print ('Original Categories:')
print (data['Item_Fat_Content'].value_counts())

print ('\nModified Categories:'
data['Item_Fat_Content']=data['Item_Fat_Content'].replace({'LF':'Low Fat',
                                                             'reg':'Regular',
                                                             'low fat':'Low Fat'})
print (data['Item_Fat_Content'].value_counts())

#understanding loc and iloc
data.loc[:,'Item_Fat_Content']
data.iloc[2,0:4]

#scince in Item_Type_Combined there are non edibles for which specifieng fat content makes no sense thus to remove it do the following
#Mark non-consumables as separate category in low_fat:
data.loc[data['Item_Type_Combined']=="Non-Consumable",'Item_Fat_Content'] = "Non-Edible"
data['Item_Fat_Content'].value_counts()

#scince scikit-learn only accepts numeric values convert the categorical fields into numeric by label encoder in preprocessing model
#Import library:
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
#New variable for outlet
data['Outlet'] = le.fit_transform(data['Outlet_Identifier'])
var_mod = ['Item_Fat_Content','Outlet_Location_Type','Outlet_Size','Item_Type_Combined','Outlet_Type','Outlet']
le = LabelEncoder()
for i in var_mod:
    data[i] = le.fit_transform(data[i])  #as Outlet_Identifier needs to be used for submission we do not change that and create Outlet instead of that. other nominal columns are directly changed in for loop

#due to the problem of weightage in these labeled columns we need to use one hot encoder which creates the dummy variebles
#for this we have get_dummies in pandas or we can also use scikit-learn
#One Hot Coding:
data = pd.get_dummies(data, columns=['Item_Fat_Content','Outlet_Location_Type','Outlet_Size','Outlet_Type',
                              'Item_Type_Combined','Outlet'])

data.dtypes

#now before building the odel we need to create the train and test data
#Drop the columns which have been converted to different types:
data.drop(['Item_Type','Outlet_Establishment_Year'],axis=1,inplace=True)

#Divide into test and train:
train = data.loc[data['source']=="train"]
test = data.loc[data['source']=="test"]

#Drop unnecessary columns:
test.drop(['Item_Outlet_Sales','source'],axis=1,inplace=True) #we drop Item_Outlet_Sales in test only as it needs to be predicted by the model
train.drop(['source'],axis=1,inplace=True)

#Export files as modified versions:
train.to_csv("train_modified.csv",index=False)
test.to_csv("test_modified.csv",index=False)

#baseline model is the one which does not recquire any prediction, eventhough the output wont make any impact, its just setting a benchmark 
#Mean based:
mean_sales = train['Item_Outlet_Sales'].mean()

#Define a dataframe with IDs for submission:
base1 = test[['Item_Identifier','Outlet_Identifier']]
base1['Item_Outlet_Sales'] = mean_sales

#Export submission file
base1.to_csv("alg0.csv",index=False)

#creating a common function which takes the algorithm and input data and performs cross validation and submit
#Define target and ID columns:
target = 'Item_Outlet_Sales'
IDcol = ['Item_Identifier','Outlet_Identifier']
from sklearn import cross_validation, metrics
def modelfit(alg, dtrain, dtest, predictors, target, IDcol, filename):
    #Fit the algorithm on the data
    alg.fit(dtrain[predictors], dtrain[target])
        
    #Predict training set:
    dtrain_predictions = alg.predict(dtrain[predictors])

    #Perform cross-validation:
    cv_score = cross_validation.cross_val_score(alg, dtrain[predictors], dtrain[target], cv=20, scoring='mean_squared_error')
    cv_score = np.sqrt(np.abs(cv_score))
    
    #Print model report:
    print ("\nModel Report")
    print ("RMSE : %.4g" % np.sqrt(metrics.mean_squared_error(dtrain[target].values, dtrain_predictions)))
    print ("CV Score : Mean - %.4g | Std - %.4g | Min - %.4g | Max - %.4g" % (np.mean(cv_score),np.std(cv_score),np.min(cv_score),np.max(cv_score)))
    
    #Predict on testing data:
    dtest[target] = alg.predict(dtest[predictors])
    
    #Export submission file:
    IDcol.append(target)
    submission = pd.DataFrame({ x: dtest[x] for x in IDcol})
    submission.to_csv(filename, index=False)


#linear regression model
from sklearn.linear_model import LinearRegression, Ridge, Lasso
predictors = [x for x in train.columns if x not in [target]+IDcol]
# print predictors
alg1 = LinearRegression(normalize=True)
modelfit(alg1, train, test, predictors, target, IDcol, 'alg1.csv')
coef1 = pd.Series(alg1.coef_, predictors).sort_values()
coef1.plot(kind='bar', title='Model Coefficients')
#as from the plot we can see although being better than the baselinr, it has higher values of coefficients whichmeans there is presence of overfitting

# to prevent overfitting use ridge(which reduces coefficient values) and lasso(which completely equates coefficients to zero)
#Ridge regression model
predictors = [x for x in train.columns if x not in [target]+IDcol]
alg2 = Ridge(alpha=0.05,normalize=True)
modelfit(alg2, train, test, predictors, target, IDcol, 'alg2.csv')
coef2 = pd.Series(alg2.coef_, predictors).sort_values()
coef2.plot(kind='bar', title='Model Coefficients')


#decision tree
from sklearn.tree import DecisionTreeRegressor
predictors = [x for x in train.columns if x not in [target]+IDcol]
alg3 = DecisionTreeRegressor(max_depth=15, min_samples_leaf=100)
modelfit(alg3, train, test, predictors, target, IDcol, 'alg3.csv')
coef3 = pd.Series(alg3.feature_importances_, predictors).sort_values(ascending=False)
coef3.plot(kind='bar', title='Feature Importances')





















