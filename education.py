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

		self.educs = []

	def get_private_colleges(self):
		"""
		get info from www.privatecollegesaustralia.com
		"""
		AUS_STATES = 'nsw vic qld wa sa tas nt act'.split()
		BASE_URL = 'https://www.privatecollegesaustralia.com'

		for st in AUS_STATES:

			print(f'state: {st}, colleges so far: {len(self.educs)}')

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

				self.educs.append(this_college)

		print(f'done. collected {len(self.educs )} colleges')

		return self

	def get_medical_colleges(self):
		"""
		http://www.cpmec.org.au/index.cfm?Do=View.Page&PageID=55
		"""
		soup = BeautifulSoup(requests.get('http://www.cpmec.org.au/index.cfm?Do=View.Page&PageID=55').text, 'lxml')

		for r in soup.find_all('tr'):

			name_ = website_ = None

			for td in r.find_all('td'):

				if not td.find('a'):
					# remove abbreviations in ()
					name_ = td.text.split('(')[0].lower().strip()
				else:
					website_ = td.find('a')['href'].strip()

				if all([name_, website_]):
					self.educs.append({'name': name_, 'website': website_})

		return self

	def get_universities(self):
		"""
		get university names and websites from www.studyinaustralia.gov.au
		"""
		soup = BeautifulSoup(requests.get('https://www.studyinaustralia.gov.au/english/australian-education/'
											'universities-and-higher-education/list-of-australian-universities').text, 'lxml')

		# grab this widget to make sure we only pick up list items located UNDER it

		wdit = soup.find('div', class_='australian-universities')

		for lst in wdit.next_siblings:
			if lst.name == 'ul':
				for li in lst.find_all('li'):
					name_ = li.text.split('-')[0].strip().lower()
					website_ = li.find('a')['href'].split('//')[-1].split('/')[0]
					self.educs.append({'name': name_, 'website': website_})

		return self

	def get_tafes(self):
		"""
		get tafe names and websites from http://www.webwombat.com.au/careers_ed/directories/tafe.htm
		"""
		# need to add user-agent because otherwise website is forbidding access
		headers = {"User-agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36"}

		soup = BeautifulSoup(requests.get('http://www.webwombat.com.au/careers_ed/directories/tafe.htm', headers=headers).text, 'lxml')

		for s in soup.find('td', class_='box').find_all('li'):

			name_ = s.text.strip().lower()
			website_ = s.find('a')['href']
			self.educs.append({'name': name_, 'website': website_})

		return self

	def get_business_schools(self):
		"""
		gt business school names ans websites from https://en.wikipedia.org/wiki/List_of_business_schools_in_Australia
		"""
		soup = BeautifulSoup(requests.get('https://en.wikipedia.org/wiki/List_of_business_schools_in_Australia').text, 'lxml')

		school_urls = defaultdict()

		for li in soup.find('div', id='mw-content-text').find_all('li'):

			all_as_ = list(li.find_all('a'))

			if (len(all_as_) == 2) or ((len(all_as_) == 1) and ('business' in all_as_[0].text.lower())):

				bs_name_ = all_as_[0].text.strip().lower()
				school_urls[bs_name_] = 'https://en.wikipedia.org' + all_as_[0]['href'] if 'wiki' in all_as_[0]['href'] else all_as_[0]['href']

		print('schools with own pages: ', len(school_urls))

		# now visit every page and find a website

		for school in school_urls:

			if 'wikipedia' not in school_urls[school]:
				self.educs.append({'name': school, 'website': school_urls[school]})
				continue

			print(school_urls[school])

			soup = BeautifulSoup(requests.get(school_urls[school]).text, 'lxml')

			infobox = soup.find('table', class_= 'infobox')

			if infobox:

				for tr in infobox.find_all('tr'):
					if 'website' in tr.text.lower():
						website_ = tr.find('a')['href']
						self.educs.append({'name': school, 'website': website_}) 
			else:
				print(f'no infobox for {school}! moving on..')

		return self

	def save(self, file):

		f_ = f'data/{file}'

		json.dump(self.educs, open(f_,'w'))

		print(f'saved {len(self.educs)} educational entities to {f_}')

if __name__ == '__main__':

	es = EducationScraper() \
		.get_business_schools() \
		.get_private_colleges() \
		.get_medical_colleges() \
		.get_universities() \
		.get_tafes() \
		.save('educs.json')