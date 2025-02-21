import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import tqdm
import re
l = []

fnames = [i for i in os.walk('Data/市领导数据/人民网地方政府资料库front/')][0][2]
for fn in fnames:
	with open('Data/市领导数据/人民网地方政府资料库front/'+fn,'r',encoding="GBK") as file:
		l.append(file.read())

full_splitted_str = []
for p in tqdm.tqdm(l):
	soup = BeautifulSoup(p)
	s = soup.select('.box01').__str__().replace('\n<br/>\n\t\t \n\t\t\t\u3000\u3000', '\n').replace(
		'[<div class="box01">\n         \n\t\t\t\u3000\u3000', '').replace('\n（人民网资料 截至2018年12月）<br/>\n</div>]',
	                                                                       '').replace('\n<br/>\n</div>]', '')
	s = s.split('\n')
	s = list(filter(lambda x: '<' not in x and '（人民网资料' not in x and x != '', s))
	res = []
	[res.append(x) for x in s if x not in res]
	full_splitted_str.append(s)

full_splitted_str_compressed = ['\n'.join(i) for i in full_splitted_str]
page_n = len(full_splitted_str)
# %%
ctnm='苏州'
def get_mayor_info(ctnm):
	"""用城市名在资料库里搜集，找到最有可能的市长人选"""
	l_ = []
	ret_list = []
	for i in range(page_n):
		if '市长' in full_splitted_str_compressed[i] and ctnm in full_splitted_str_compressed[i]:
			l_.append(full_splitted_str[i])
	for p in l_:
		if len(p) < 4:
			continue
		for i in range(-1, -3, -1):
			if '市长' in p[i] and ctnm in p[i]:
				ret_list.append(p)
	if not ret_list:
		return
	if len(ret_list) == 1:
		return ret_list[0][0]
	else:
		rl = [ret_list[i] == ret_list[i+1] for i in range(len(ret_list)-1)]
		if sum(rl) == len(rl):
			return ret_list[0][0]
		else:
			res = []
			[res.append(x) for x in ret_list if x not in res]
			return res



def mayor_info_by_name(name, ctnm=''):
	for i in range(page_n):
		if name in full_splitted_str_compressed[i]:
			print(full_splitted_str[i])

mayor_info_by_name('李爱武')
r = get_mayor_info('苏州')


#%%
d = pd.read_csv('Data/276城_3source_by_ct_V3.csv')
data = d[['ct_shortname', 'citycode']].copy()
dt = {'mayor': '', 'mayor_sex': '', 'mayor_race': '',
      'mayor_birth': '', 'mayor_joinwork': '',
      'mayor_partytime': ''}  # ,

for col_n in dt.keys():
	data[col_n] = ''
data['records'] = ''

l_toadd = []
for ctn in tqdm.tqdm(data.ct_shortname):
	info = 0
	try:
		info = get_mayor_info(ctn)
	except:
		pass
	if isinstance(info, str):
		data.loc[data.ct_shortname == ctn, 'records'] = info
	else:
		# print(info)
		pass

# %% 初步process减少工作量
# a = list(d.prov.unique())
# for i in range(len(a)):
# 	a[i] = a[i].replace('省','').replace('自治区','').replace('回族','').replace('壮族','').replace('维吾尔','')
# prov_short_list = a

def info_split(s):
	dt = {'mayor':'', 'mayor_sex':'', 'mayor_race':'',
	         'mayor_birth':'', 'mayor_joinwork':'',
	         'mayor_partytime':''}#,
	      # 'mayor_edu':''} ,'mayor_origin':''
	if not s:
		return dt
	s = re.split('，|。',s)
	if '0' in s[0]:
		return dt
	dt['mayor'] = s[0]
	if '男' in s:
		dt['mayor_sex'] = '男'
	elif '女' in s:
		dt['mayor_sex'] = '女'
	for t in s:
		if all(x in t for x in ['年', '月', '19', '生']) and len(t) < 20 and not dt['mayor_birth']:
			dt['mayor_birth'] = t
		# elif any(x in t for x in prov_short_list) and ('人' in t or '籍贯' in t) and :
		elif all(x in t for x in ['年', '月', '19', '参加工作']) and not dt['mayor_joinwork']:
			dt['mayor_joinwork'] = t
		elif all(x in t for x in ['年', '月', '19', '党', '入']) and not dt['mayor_partytime']:
			dt['mayor_partytime'] = t
		elif '族' in t and len(t) < 7 and not dt['mayor_race']:
			dt['mayor_race'] = t
	return dt


for i in range(data.shape[0]):
	data.iloc[i]['records'] = get_mayor_info(data.iloc[i]['ct_shortname'])
	dt = info_split(data.iloc[i]['records'])
	for col_n in dt.keys():
		data.loc[i, col_n] = dt[col_n]


# %%
data['prov'] = d.prov.copy()
data.to_excel('Data/市领导数据/人民网-市长-V0.5.xlsx', index=True)
data.mayor_birth.unique()

# %% 经过人工处理之后再来finalize

data = pd.read_excel('Data/市领导数据/人民网-市长-V0.8-人工.xlsx')
for i in range(data.shape[0]):
	if data.iloc[i]['prov'] == '湖北省':
		continue
	if pd.isna(data.iloc[i]['mayor']) and pd.isna(data.iloc[i]['mayor_birth']) and pd.isna(data.iloc[i]['mayor_joinwork']):
		dt = info_split(data.iloc[i]['records'])
		for col in dt.keys():
			if pd.isna(data.iloc[i][col]):
				data.loc[i, col] = dt[col]
data.to_excel('Data/市领导数据/人民网-市长-V0.9-人工.xlsx', index=False)
# %%
data = pd.read_excel('Data/市领导数据/人民网-市长-V0.95-人工.xlsx')
def ext_datetime(s):
	new = ''
	for c in s:
		if c in [str(i) for i in range(10)]+['年', '月']:
			new += c

	return new.replace('年', '.').replace('月','')

# data['mayor_partytime'] = data['mayor_partytime'].apply(ext_datetime).apply(pd.to_datetime)
data['mayor_joinwork'] = data['mayor_joinwork'].apply(ext_datetime).apply(pd.to_datetime)
data['mayor_birth'] = data['mayor_birth'].apply(ext_datetime).apply(pd.to_datetime)

data['mayor_age'] = (pd.to_datetime('2020-02-01') - data['mayor_birth']).astype('<m8[Y]')
# data['mayor_party_age'] = (pd.to_datetime('2020-02-01') - data['mayor_partytime']).astype('<m8[Y]')
data['mayor_work_age'] = (pd.to_datetime('2020-02-01') - data['mayor_joinwork']).astype('<m8[Y]')

data['mayor'] = data.mayor.apply(lambda s:s.replace('\u3000', '').replace(' ', '').replace('现任台州市委副书记', '') )
data['mayor_sex'].fillna('男', inplace=True)
data['mayor_race'].fillna('汉族', inplace=True)
data.to_excel('Data/市领导数据/人民网-市长-V1.xlsx', index=False)

# %%
i = 7;print(d.ct_shortname[i])
print(get_mayor_info(d.ct_shortname[i]))
get_mayor_info(d.ct_shortname[i])
print(d.ct_shortname[i])