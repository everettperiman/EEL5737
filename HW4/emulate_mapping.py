import random

def mapping_algo(nservers, block_number, data):
	stripe = block_number // (nservers - 1)
	parity = stripe % nservers
	column = block_number % nservers
	print("Stripe {}, Column {}, Parity in Stripe {}, Data {}".format(stripe, column, parity, client[stripe][column]))
	#return server, position

length = 100
servers = 4

client_data = [random.randint(0,3) for i in range(length)]

index = 0
client = []
for i in range(int(length/(servers-1))):
	row = []
	for j in range(servers):
		if j == i % servers:
			row.append("P")
		else:
			row.append(client_data[index])
			index = index + 1
	client.append(row)
	print(index)
	print(row)
mapping_algo(4, 96, client)
#client = [random.randint(0,3) for i in range(length)]
#@server = ["P" for i in client if length mod 4]
server_a = []
server_b = []
server_b = []
server_d = []
