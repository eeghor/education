from bs4 import BeautifulSoup
import requests
import os
from collections import defaultdict
import re
from unidecode import unidecode
import json

class EducationScraper:

	def __init__(self):

		# create a data directory if it doesn't exits

		if not os.path.exists('data'):
			os.mkdir('data')

		self.colleges = []

	def get_private_colleges(self):
		"""
		get info from www.privatecollegesaustralia.com
		"""
		AUS_STATES = 'nsw vic qld wa sa tas nt act'.split()
		BASE_URL = 'https://www.privatecollegesaustralia.com'

		for st in AUS_STATES:

			print(f'state: {st}, colleges so far: {len(self.colleges)}')

			soup = BeautifulSoup(requests.get(f'{BASE_URL}/{st}.html').text, 'lxml')

			pick_this = True  # will surely process the first found paragraph

			for p in soup.find_all('div', class_='paragraph', style="text-align:left;"):

				if not pick_this:
					pick_this = True
					continue

				this_college = defaultdict()

				# typical parent class is wsite-section-elements but for multicolumns it's wsite-multicol-col

				pparent = p.parent

				if not pparent:
					print(f'note: div without a parent!')
					continue

				if pparent['class'] == 'wsite-multicol-col':
					pick_this = False

				try:
					this_college['name'] = unidecode(p.find('strong').text.lower()).strip()
				except:
					this_college['name'] = None

				for s in p.find_all('span'):

					span_txt_ = s.text.strip().lower()

					# does it look like a address? it wuld have to be like 770 George St, Sydney, ..
					if re.search(r'\s*\d+\s+\w+\s+\w+\,*\s+', span_txt_):
						this_college['address'] = span_txt_

					if span_txt_.startswith('phone'):
						this_college['phone'] = ''.join([_ for _ in span_txt_ if _.isdigit()])

					email_or_web = s.find_all('a')

					if email_or_web:

						for a in email_or_web:

							if a.has_attr('href') and ('@' in a['href']) and ('email' not in this_college):
								this_college['email'] = a['href'].split(':')[-1].strip()

							if a.has_attr('href') and \
								(('http' in a['href']) or ('www.' in a['href'])) and \
								('website' not in this_college):
								this_college['website'] = a['href'].strip()

					if this_college.get('website', None):
						this_college['labels'] = [lab.strip() for lab in span_txt_.replace('.','').split(',') if lab.strip()]

				self.colleges.append(this_college)

		print(f'done. collected {len(self.colleges )} colleges')

		return self

	def save(self, file):

		json.dump(self.colleges, open(f'data/{file}','w'))

if __name__ == '__main__':

	es = EducationScraper() \
		.get_private_colleges() \
		.save('private_colleges.json')