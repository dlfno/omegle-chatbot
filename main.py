from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import sys
import select
from time import sleep
from random import choice
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
import logging

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s - %(message)s')
logging.disable(logging.CRITICAL)


def input_with_timeout(prompt, timeout):
	sys.stdout.write(prompt)
	sys.stdout.flush()
	ready, _, _ = select.select([sys.stdin], [], [], timeout)
	if ready:
		return sys.stdin.readline().rstrip('\n')
	raise ValueError('Timeout Expired')


def solve_recaptcha(driver_ref):
	sleep(3)

	recaptcha_iframe = driver_ref.find_elements_by_css_selector("iframe[width='304']")

	if recaptcha_iframe:
		recaptcha_iframe[0].click()

		sleep(3)

		recaptcha_div = driver_ref.find_elements_by_css_selector('body > div')[-1]
		
		if 'visible' in recaptcha_div.get_attribute('style'):
			recaptcha_iframe = driver_ref.find_element_by_css_selector("body > div > div > iframe[title='recaptcha challenge']")
		
			driver_ref.switch_to.frame(recaptcha_iframe)

			sleep(3)

			audio_button = driver_ref.find_element_by_css_selector("button[id='recaptcha-audio-button']")
			audio_button.click()

			sleep(2)

			while True:
				sleep(2)

				text = ''
				while not text:
					play = driver_ref.find_element_by_css_selector("button[class='rc-button-default goog-inline-block']")
					play.click()

					sleep(4)

					play = driver_ref.find_element_by_css_selector("button[class='rc-button-default goog-inline-block']")
					play.click()

					sleep(4)

					text = input('What did you hear? [empty play again] ')

					sleep(2)

					text_box = driver_ref.find_element_by_css_selector("input[id='audio-response']")

				text_box.send_keys(text)

				sleep(3)

				text_box.send_keys(Keys.ENTER)

				sleep(2)

				if 'hidden' in recaptcha_div.get_attribute('style'):
					driver_ref.switch_to.default_content()
					break

			print('Recaptcha done!')

# if len(sys.argv) in range(2, 4):
# 	interests_file = sys.argv[1] if sys.argv[1].endswith('.txt') else sys.argv[1] + '.txt'

# 	try:
# 		with open(interests_file, 'r') as f:
# 			interests += f.read()
# 	except FileNotFoundError:
# 		print('Invalid interests file.')
# 		sys.exit()
# elif len(sys.argv) > 3:
# 	print('Invalid command.')
# 	print(f'Try: python {__file__} [interests_file_txt] [lang]')
# 	sys.exit()

driver = webdriver.Firefox()

# Window Config

# Half screen in second monitor
# driver.set_window_position(636, 0)
# driver.set_window_size(955, 1050)
# driver.set_window_position(961, 0)

# Full screen in monitor
driver.maximize_window()

driver.get('https://www.omegle.com')

sleep(3)

class OmegleChatBot:
	__body_elem = driver.find_element_by_tag_name("body")
	__start_new_chat = ''

	def __init__(self, chatbot='Omegle', language='en', interests=''):
		self.chatbot = ChatBot(chatbot)

		self.language = language
		if language == 'pt':
			interests += 'Português, Brasil'

		self.interests = interests

		if self.interests:
			new_topic = driver.find_element_by_css_selector("input[class='newtopicinput'][type='text']")
			new_topic.send_keys(interests, Keys.ENTER)

		driver.find_element_by_css_selector("img[id='textbtn']").click()

	def chat_status(self):
		status_logs = [elem.text for elem in driver.find_elements_by_css_selector("p[class='statuslog']")]

		if not status_logs or status_logs and status_logs[-1] == 'Connecting to server...':
			return 'Waiting' 
		elif status_logs[-1] in ['Stranger has disconnected.', 'You have disconnected.']:
			return 'Disconnected'
		else:
			return 'Active'


	def filter_messages(self, who):
		tag_class = 'youmsg' if who.lower() == 'me' else 'strangermsg'
		msg_elems = driver.find_elements_by_css_selector(f"p[class='{tag_class}'] span")
		msgs = [msg.text for msg in msg_elems]

		return msgs


	def history_messages(self):
		source_history_elems = driver.find_elements_by_css_selector("strong[class='msgsource']")
		source_history = [elem.text for elem in source_history_elems]

		msg_history_elems = driver.find_elements_by_xpath("//strong[@class='msgsource']/following-sibling::span")
		msg_history = [elem.text for elem in msg_history_elems]

		history = list(zip(source_history, msg_history))

		return history


	def stranger_active(self, num_of_checks=5, secs=1):
		msg_history = self.history_messages()

		if msg_history and msg_history[-1][0] == 'Stranger:':
			return True	
		else:
			for _ in range(num_of_checks):
				old_str_msgs = self.filter_messages(who='stranger')

				sleep(secs)

				new_str_msgs = self.filter_messages(who='stranger')
				
				if old_str_msgs != new_str_msgs:
					return True

		return False


	def send_msg(self, msg, chars_per_sec):
		"""
		:msg: Message to send.
		
		No return
		"""
		delay = len(msg) / chars_per_sec

		self.__body_elem.send_keys(msg)
		sleep(delay)
		self.__body_elem.send_keys(Keys.ENTER)
		sleep(delay / 2)


	def skip_chat(self, delay=5):
		if delay > 0:
			try:
				self.__start_new_chat = input_with_timeout('Start new Chat? ', delay)
			except Exception as err:
				print(err)
				self.__start_new_chat = 'yes'
		else:
			self.__start_new_chat = 'yes'

		if self.__start_new_chat and self.__start_new_chat.lower()[0] == 'y':

			# Stop chat
			self.__body_elem.send_keys(Keys.ESCAPE)
			self.__body_elem.send_keys(Keys.ESCAPE)

			# New chat
			self.__body_elem.send_keys(Keys.ESCAPE)
		
		return self.__start_new_chat


	def start_chat(self):
		while self.chat_status() == 'Waiting':
			sleep(3)

		self.__start_new_chat = self.__start_new_chat if self.history_messages() else ''

		if self.chat_status() == 'Active' and not self.__start_new_chat and not self.stranger_active():
			self.__start_new_chat = self.skip_chat(delay=4)

		if self.chat_status() == 'Disconnected':
			if self.history_messages():
				with open('history_messages.txt', 'a') as f:
					f.write(f"{'-' * 30}\n")
					for sender, message in self.history_messages():
						f.write(f'{sender:9} {message}\n')

			self.__body_elem.send_keys(Keys.ESCAPE)
	

	def start(self, typing_speed=5, msgs=[['Hello. How are you?'], ['Hey, what\'s up?']]):
		self.start_chat()
		first_msgs = choice(msgs)[::]

		while self.chat_status() == 'Active' and self.stranger_active(10):
			last_stranger_msg = self.filter_messages(who='stranger')[-1]
			if last_stranger_msg:
				response_msg = str(self.chatbot.get_response(last_stranger_msg))
			elif first_msgs and not self.history_messages():
				response_msg = first_msgs[0]
				first_msgs = first_msgs[1:]

			self.send_msg(response_msg, typing_speed)


chatbot = OmegleChatBot('Omegle')

if __name__ == '__main__':
	solve_recaptcha(driver)

	while True:
		try:
				chatbot.start()
		except Exception as err:
			print('An error occured: ')
			print(err)

# TODO Solve bug that is skipping chats where stranger don't send message first
# TODO Get the last message of user as a concatenation of all sent messages after bot last message
