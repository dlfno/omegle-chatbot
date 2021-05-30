from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer

chatbot = ChatBot('Omegle')
trainer = ListTrainer(chatbot)

# trainer.train([
# 	"How are you?",
# 	"I am good.",
# 	"That is good to hear.",
# 	"Thank you",
# 	"You are welcome.",
# ])
# trainer.train(["What's up?", "Nothing much. Just chilling out and u?"])
# trainer.train(["Where u from?", "United States and u?"])

trainer.train(['Nothin', 'Oh ye, I see'])
