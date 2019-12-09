import socket
import struct
import sys
import time
import pickle
import math
import select
import sys
import _thread as thread


# Send message
def senderthread(threadName):
	multicast_group = ('224.3.29.71', 5007)
	# Untuk hop count
	hop = 0
	global id_node, lctn
	# Create the datagram socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# Set a timeout so the socket does not block indefinitely when trying
	# to receive data.
	sock.settimeout(0.2)

	# Set the time-to-live for messages to 1 so they do not go past the
	# local network segment.
	ttl = struct.pack('b', 1)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

	while True:
		print ("Input Message : ")
		message = input()
		print ("Input ID Tujuan : ")
		id_tujuan = input()

		# Paket data yang akan dikirim berupa array
		data = []
		data.append(message) # data[0]
		data.append(lctn) # data[1]
		data.append(hop) # data[2]
		data.append(id_node) # data[3]
		data.append(id_tujuan) # data[4]
		# Array data harus mengalami pickle terlebih dahulu
		dataKirim = pickle.dumps(data)

		# Send data to the multicast group
		print ("Sending Message : ", message)
		sock.sendto(dataKirim, multicast_group)


# Receive message
def receiverthread(threadName):
	multicast_group = '224.3.29.71'
	multicast = ('224.3.29.71', 5007)
	server_address = ('', 10000)

	# Create the socket
	#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	#s.connect(("8.8.8.8", 80))
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((multicast_group, 5007))

	# Tell the operating system to add the socket to the multicast group
	# on all interfaces.
	group = socket.inet_aton(multicast_group)
	mreq = struct.	pack('4sL', group, socket.INADDR_ANY)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	while True:
		dataTerima, address = sock.recvfrom(1024)
		data =  pickle.loads(dataTerima)
		receiveBuffer(dataTerima, address)


# Proses pesan masuk
def receiveBuffer(dataTerima, address):
	data =  pickle.loads(dataTerima)	
	message = data[0]
	location = data[1]
	hop = data[2]
	id_sumber = data[3]
	id_tujuan = data[4]
	global id_node, batas, batas_waktu, batas_waktu, batas_hop
	if id_sumber != id_node:
		print >>sys.stderr, 'received %s bytes from %s' % (len(message), address)
	print ('message :', message)
	print ('location :', location)
	print ('hop :', hop)
	print ('id sumber :', id_sumber)
	print ('id node :', id_tujuan)
	global pkt_count
	if pkt_count == 0:
		list_data[pkt_count] = [data, "YES"] # Masukin data ke list data
		pkt_count += 1
	else:
		
		for x, y in list_data.items():
			print ('tes',list_data.items())
			# Kalo datanya sama di update
			if message == y[0][0] and location == y[0][1] and id_tujuan == y[0][4]:
				#menambahkan jarak tempuh tiap menit 
				Longitude, Latitude = location
				Longitude = Longitude + 0.00000001
				Latitude = Latitude + 0.00000001
				location = Longitude, Latitude
				distance = haversine(location, lctn) * 1000
				print ("Tentang waktu",batas, batas_waktu)
				print ("Tentang jarak",distance, batas_jarak)
				print ("Tentang hop",hop, batas_hop)
				if id_sumber != id_node and hop < y[0][2]:
					continue
				elif id_sumber ==  id_node and batas < batas_waktu + 1 and distance < batas_jarak and hop < batas_hop:
					data = []
					data.append(message) # data[0]
					data.append(location) # data[1]
					data.append(hop) # data[2]
					data.append(id_sumber) # data[3]
					data.append(id_tujuan) # data[4]
					list_data[x] = [data, "YES"]

				elif id_sumber !=  id_node and batas < batas_waktu + 1 and distance < batas_jarak and hop < batas_hop:
					data = []
					hop = hop + 1
					data.append(message) # data[0]
					data.append(location) # data[1]
					data.append(hop) # data[2]
					data.append(id_node) # data[3]
					data.append(id_tujuan) # data[4]
					list_data[x] = [data, "YES"]

				elif batas >= batas_waktu + 1 or distance >= batas_jarak or hop >= batas_hop:
					print ("masuk")
					list_data[x] = [data, "NO"]

			else:
				list_data[pkt_count] = [data, "YES"] # Masukin data ke list data
				pkt_count += 1		
	
	for x, y in list_data.items():
		print ("Array ke -", x)
		print ("Mempunyai data", y[0])
		print ("Dengan status", y[1])
	
# Untuk proses buffer
def checkthread(threadName):
	while True:
		global batas
		timelock = time.localtime(time.time())
		awal = timelock[4]	
		for x, y in list_data.items():
			if y[1] == "NO":
				list_data.pop(x)
			elif awal == batas:
				batas = awal + 1
				forward(y[0])


# Fungsi untuk forward data yang sudah masuk
def forward(dataTerima):
	multicast_group = ('224.3.29.71', 10000)

	# Create the datagram socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	# Set a timeout so the socket does not block indefinitely when trying
	# to receive data.
	sock.settimeout(0.2)

	# Set the time-to-live for messages to 1 so they do not go past the
	# local network segment.
	ttl = struct.pack('b', 1)
	sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

	# print "Forwarding Message : ", dataTerima[0]
	dataKirim = pickle.dumps(dataTerima)
	sock.sendto(dataKirim, multicast_group)


# Fungsi untuk menghitung jarak antara 2 lokasi
def haversine(coord1, coord2):
    R = 6372800  # Earth radius in meters
    # Latitude dan Longitude
    lat1, lon1 = coord1
    lat2, lon2 = coord2
  
    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + \
        math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Main function
try:
	localtime = time.localtime(time.time())
	batas = localtime[4]
	batas_hop = 2
	batas_waktu = batas + 2 # Dalam menit
	batas_jarak = 100
	lctn = [51.5073219,  -0.1276474] # Lokasi palsu kita
	list_data = {} # Untuk masukin data yang ada di server
	pkt_count = 0 # Inisialisasi jumlah data yang dikirim
	print ('Node id')
	id_node = input() # inisialisasi id sumber
	id_pernah = []
	thread.start_new_thread(senderthread,("Sender",))
	thread.start_new_thread(receiverthread,("Receiver",))
	thread.start_new_thread(checkthread,("Check",))
except:
	print ("Error: unable to start new thread")

while 1:
	pass
