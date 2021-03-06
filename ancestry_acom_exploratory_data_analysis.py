# -*- coding: utf-8 -*-
"""Ancestry ACOM Exploratory Data Analysis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1ZpDWn7Vzy9VhSOxT7OvCD974g0d1nAGB

## **EDA for Ancestry Cross-Sales: DNA Products to ACOM Subscriptions**

---
"""

#importing the packages to be used
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from itertools import compress

"""### Retrieve the Data"""
import os
# Link retrieved from Download Link URL
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(ROOT_DIR, 'take-home_exercise_data.csv')
raw_data = pd.read_csv(path)

#Notify users of the time required for the below
print("Gathering data; this may take a few moments...")

# Get the total number of orders
numrows = len(np.array(raw_data["prospectid"]))
# Get the total number of customers; the idea here is to be able to see right off the bat how many extra orders there were
num_unique_of_customers = len(np.unique(raw_data["prospectid"]))

# Compile a list of all the unique customers who were cross-sells
cross_sell_ids = []
for i in range(numrows):
  id_num = raw_data["prospectid"][i]
  if id_num in cross_sell_ids:
    continue
  elif raw_data["xsell_day_exact"][i]<=120 and raw_data["xsell_gsa"][i] == 1:
    cross_sell_ids.append(id_num)
  else:
    continue

# This tells us what portion of total customers are cross-sells
# What % of customers cross sell to subscription?
'%s%s of customers cross sell to subscription' % (round(len(cross_sell_ids) / num_unique_of_customers * 100,2),'%')

"""### Clean the Data set"""

# Remove irrelevant pieces
clean0 = raw_data.drop(columns = ['Unnamed: 0','prospectid', 'ordernumber'])
# Check to see if NAs are reasonable
# Looks like if dna test is not activated, days to get result should be -1; if xsell_gsa is 0, then xsell_day_exact is NaN
# Assumption: any row in which the dnatestactivationdayid is NA/NaN represents false data and not a true customer
clean0[clean0.dnatestactivationdayid.isna()&(clean0.daystogetresult_grp!="-1")].shape[0] == 0 
clean0[(clean0.xsell_gsa!=0)&(clean0.xsell_day_exact.isna())].shape[0] == 0
# Looks good. NaN values seems reasonable
# Change dates to date object
clean0['dnatestactivationdayid'] = clean0['dnatestactivationdayid'].astype('datetime64[ns]')
clean0['ordercreatedate'] = clean0['ordercreatedate'].astype('datetime64[ns]')

# Check for irregular names that could be duplicates in each factor column
a = []
for i in clean0.select_dtypes(include = 'object').columns:
  a.append(clean0[i].value_counts(dropna=False))

# Can't find any spelling/capital letter errors.

# Create potentially useful variables
# If xsell_day_exact is less than 120 days old become and have xsell_gsa we should be 1
clean0['y'] = ((clean0.xsell_day_exact<=120))&(clean0.xsell_gsa == 1)
# Is column valid? 
np.sum(clean0.xsell_gsa != clean0.y)!=clean0.shape[0] # Looks like we needed to create y

# Synthesize a new causal variable from two pre-existing data points: Days to DNA activation since order creation
clean0['daystodnaactivation'] = (clean0['dnatestactivationdayid']-clean0['ordercreatedate'])/np.timedelta64(1,'D')
# Remove dates and regtenure (We already know that those) for Analysis
df = clean0.drop(columns = ['dnatestactivationdayid','ordercreatedate'])
df

"""## **Exploring the Data**

---
"""

# What % of orders cross sell to subscription?
'%s%s of orders cross sell to subscription' % (np.round(np.mean(df.y)*100,2),'%')

"""### Email Registration Tenure"""

# Does variation in number of days since registering an email seem to play a role in determining whether customers purchase ACOM Subscriptions?
pd.pivot_table(df, values='y',
               columns=['regtenure'], aggfunc=np.sum, fill_value=0).plot.bar()

# Seems like there is variation between factor levels which will be useful for a logistic regression.
# Longer time customers and those that order prior to registration seem to cross sell more.
# Those that are registered for more than 4 months may have had ample time to explore options.
# Those that order prior to registration may know what they are looking for.
# We can validate this by looking at Order Prior to Reg individuals and checking if their xsell days are short.

# Column 'not y' are the orders that did not cross sell.
df['not_y'] = np.array([not i for i in np.array(df.y)])
pd.pivot_table(df, values='not_y',
               columns=['regtenure'], aggfunc=np.sum, fill_value=0).plot.bar()

regtenure=list(np.array(df.regtenure))
cross_sell = np.array(df.y)

# unique_regtenure=np.unique(regtenure)
unique_regtenure = ['More than 120 days old','<=90 days','<=60 days','<=30 days','<=20 day','<=10 days','Order prior to reg','No Reg Date']
cross_fractions = []
total_regtenures = []
cross_sell_types = []
for unique_rt in unique_regtenure:
  tot = regtenure.count(unique_rt)
  total_regtenures.append(tot)

  reg_cross_sold = list(compress(regtenure, cross_sell))
  frac = reg_cross_sold.count(unique_rt)
  cross_sell_types.append(frac)
  cross_fractions.append(frac/tot)

for i in range(len(unique_regtenure)):
  print(np.round(cross_fractions[i]*100,2)," ",unique_regtenure[i], "out of ",total_regtenures[i])

plt.bar(list(range(len(unique_regtenure))), cross_fractions,tick_label=unique_regtenure)

plt.bar(list(range(len(unique_regtenure))),np.array(cross_sell_types)/(np.mean(df.y)*len(df.y)),tick_label=unique_regtenure)

"""Most cross sales are from customers who registered an email after they ordered or registered 120 days before ordering.
The group of people who are most likely to buy a subscription are those who register their email after ordering.

### Customer Types
"""

pd.pivot_table(df, values='y',
               columns=['customer_type_group'], aggfunc=np.sum, fill_value=0).plot.bar()

pd.pivot_table(df, values='not_y',
               columns=['customer_type_group'], aggfunc=np.sum, fill_value=0).plot.bar()

# Which customer types seem to cross-sell the most?
customer_types = list(np.array(df.customer_type_group))
unique_customers = np.unique(customer_types)

regtenure=list(np.array(df.regtenure))
cross_sell = np.array(df.y)

cross_fractions = []
total_customer_types = []
cross_sell_types = []
for unique_ct in unique_customers:
  tot = customer_types.count(unique_ct)
  total_customer_types.append(tot)

  customer_cross_sold = list(compress(customer_types, cross_sell))
  frac = customer_cross_sold.count(unique_ct)
  cross_sell_types.append(frac)
  cross_fractions.append(frac/tot)

for i in range(len(unique_customers)):
  print(np.round(cross_fractions[i]*100,2)," ",unique_customers[i], "out of ",total_customer_types[i])

plt.bar(list(range(len(unique_customers))), cross_fractions,tick_label=unique_customers)

plt.bar(list(range(len(unique_customers))),np.array(cross_sell_types)/(np.mean(df.y)*len(df.y)),tick_label=unique_customers)

"""Cross sales most often come from customers who had already registered before placing the order. They are also the most likely customers to purchase a subscription.
Those who already have a subscription are least likely to purchase another. That said, it is not clear what "registration" means in this context since it seems that the data suggests otherwise with respect to email registration.

### Weeks between Purchase and Obtaining Results
"""

# Does the delay or time elapsed between ordering a DNA product and receiving the results from Ancestry help determine whether a customer purchases an ACOM subscription?
results_delay = list(np.array(df.daystogetresult_grp))
unique_delays = ['1 week','2 weeks', '3 weeks', '4 weeks','5 weeks', '6 weeks', '7 weeks', '8 weeks', '9 weeks', '>10weeks','-1']
# unique_delays = np.unique(results_delay)

cross_fractions = []
total_delay_types = []
cross_sell_delay_types = []
for unique_dt in unique_delays:
  tot = results_delay.count(unique_dt)
  total_delay_types.append(tot)

  results_cross_sold = list(compress(results_delay, cross_sell))
  frac = results_cross_sold.count(unique_dt)
  cross_sell_delay_types.append(frac)
  cross_fractions.append(frac/tot)

for i in range(len(unique_delays)):
  print(np.round(cross_fractions[i]*100,2)," ",unique_delays[i], "out of ",total_delay_types[i])

plt.bar(list(range(len(unique_delays))), cross_fractions,tick_label=unique_delays)

plt.bar(list(range(len(unique_delays))),np.array(cross_sell_delay_types)/(np.mean(df.y)*len(df.y)),tick_label=unique_delays)

"""The delay between the order and results has little effect on subsequent purchase of subscription.
The largest category of customers who purchased a subscription are those who never activated their DNA test, but this category also contains the largest number of people (3x the size of the next largest).

### Traffic Visit Channel
"""

# Does the Traffic Visit Channel play a role in determining the likelihood of a customer purchasing an ACOM Subscription?
visit_channel = list(np.array(df.dna_visittrafficsubtype))
unique_channels = np.unique(visit_channel)

cross_fractions = []
total_channel_types = []
cross_sell_channel_types = []
for unique_ch in unique_channels:
  tot = visit_channel.count(unique_ch)
  total_channel_types.append(tot)

  channels_cross_sold = list(compress(visit_channel, cross_sell))
  frac = channels_cross_sold.count(unique_ch)
  cross_sell_channel_types.append(frac)

  if tot == 0:
    cross_fractions.append(0)
  else:
    cross_fractions.append(frac/tot)

for i in range(len(unique_channels)):
  print(np.round(cross_fractions[i]*100,2)," ",unique_channels[i], "out of ",total_channel_types[i])

plt.bar(list(range(len(unique_channels))), cross_fractions,tick_label=unique_channels)

"""The fraction of the customers in a category that purchased a subscription. Over 60% of customers who purchased an Ancestry product through 'FTM Software Integration' channel subsequently purchased a subscription."""

plt.bar(list(range(len(unique_channels))),np.array(cross_sell_channel_types)/(np.mean(df.y)*len(df.y)),tick_label=unique_channels)

cross_sell_fractions = np.array(cross_sell_channel_types)/(np.mean(df.y)*len(df.y))
for i in range(len(unique_channels)):
  print(np.round(cross_sell_fractions[i]*100,2)," ",unique_channels[i])

"""The most popular channel for cross sales is 'direct core homepage`. The runners up are 'paid search – dna brand', 'Email Campaigns', and 'paid search – core brand.'

## **Conclusion**

---

Further analysis could be done by the following:

(1) Using the following code found above [clean0['daystodnaactivation'] = (clean0['dnatestactivationdayid']-clean0['ordercreatedate'])/np.timedelta64(1,'D')]. This piece of code creates a new column that contains the number of days elapsed between the order date of a DNA product and the activation of it. We could create categories similar to other variables above (<1 week, <2 weeks, <3 weeks, etc) and then see what correlation there is, if any, between the time customers take to activate their DNA product after purchasing it and the purchase of an ACOM subscription.

(2) We could do a logistic regression using scikit learn to place the output (y) as a binary value of either 0 or 1 (yes, no) in the likelihood of customers cross-selling, with each of the factors analyzed above as the x variables or causal inputs.
"""
