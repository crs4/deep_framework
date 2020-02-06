class SlidingWindow:

	def __init__(self, size):
		self.size = size
		self.items = []

	def add_item(self,item):
		if len(self.items) == self.size:
			self.remove_item()

		self.items.append(item)

	def remove_item(self):
		del self.items[0]

	

	