
const monitor_address = process.env.MONITOR_ADDRESS || '0.0.0.0'
const monitor_port = process.env.MONITOR_STATS_OUT || '3000'
const algs = process.env.ALGS
const face_port = process.env.FACE_PORT

const protocol = process.env.PROT || 'tcp://'

const appPath = process.cwd() + '/deep_app/static/index.html' // '/home/deepframework/server/deep_app/templates/index.html'
const serverPort = process.env.SERVER_PORT || 8000

const express  = require('express');
const app = express();
const https = require("https")
const fs = require("fs")
const server = https.createServer({
	key: fs.readFileSync('./cert/key.pem'),
	cert: fs.readFileSync('./cert/cert.pem'),
	// ca: fs.readFileSync('./cert/ca.cert.pem')
}, app);

/**
 * Hyperpeer server
 */
const HpServer = require('hyperpeer-node');
const verifyPeer = function (type, peerId, peerKey) {
	return true;
}
const hpServer = new HpServer({ server: server, verifyPeer: verifyPeer });

const zmq = require('zeromq');

const face_sock = zmq.socket('pair');
// const person_sock = zmq.socket('pair');
const monitor_sock = zmq.socket('sub');


face_sock.bind(protocol +'*:'+ face_port);
// person_sock.bind(protocol +'*:'+ person_port.toString());
monitor_sock.connect(protocol + monitor_address + ':' + monitor_port);
monitor_sock.subscribe('');





app.get('/api/faces_stream', function(request, response){

	response.writeHead(200, {
	'Content-Type': 'text/event-stream',
	'Cache-Control': 'no-cache',
	'Connection': 'keep-alive'
	});

	face_sock.on("message", function(data) {
		response.write("data: " + data.toString() + "\n\n");
	});
});

// app.get('/api/body_stream', function(request, response){

// 	response.writeHead(200, {
// 	'Content-Type': 'text/event-stream',
// 	'Cache-Control': 'no-cache',
// 	'Connection': 'keep-alive'
// 	});

// 	person_sock.on("message", function(data) {
// 		response.write("data: " + data.toString() + "\n\n");
// 	});
// });
app.get('/api/algs', function(request, response){
	const algs_arr = algs.split(",");
	response.json({algs_list: algs_arr});

});

app.get('/api/stats', function(request, response){

	response.writeHead(200, {
	'Content-Type': 'text/event-stream',
	'Cache-Control': 'no-cache',
	'Connection': 'keep-alive'
	});

	monitor_sock.on("message", function(data) {
		response.write("data: " + data.toString() + "\n\n");
	});
});

/*

io.on('connection',function(socket){

	console.log('connection');

    socket.on('start stream',function(image){
        
    	console.log('stream');


	    source_sock.on("message", function(data,frame) {

			data = data.toString();
			json_data = JSON.parse(data);
			frame_data = json_data["payloads"][0]
			frame_type = frame_data["dtype"]; 
			frame_shape = frame_data["shape"];
			frame_height = parseInt(frame_shape[0], 10);
			frame_width = parseInt(frame_shape[1], 10);
			

			const view = new Uint8Array(frame);
			const frame_uint8 = nj.uint8(view); 
			const res_frame = frame_uint8.reshape(frame_width,frame_height,3);
			

			
			// const rawImageData = {
			//   data: res_frame.selection.data,
			//   width: frame_width,
			//   height: frame_height
			// };
			// const jpegImageData = jpeg.encode(rawImageData, 50);
			

			//buf = Buffer.from(jpegImageData.data);


			//buf = Buffer.from(res_frame.selection.data);
			//console.log(buf);
			//const buffer_img = res_frame.selection.data;
			//const b64encoded = Uint8ToString(jpegImageData);
			//console.log(b64encoded);

			//const frame_array = nj.array(frame);
			//const frame_uint8 = nj.uint8(frame_array); 
			//console.log(frame.readInt8());

			//const res_frame = frame_array.reshape(frame_width,frame_height,3);
			//console.log(res_frame);

			//const res_uint8 = nj.uint8(res_frame);


			//const buffer_img = frame_uint8.selection.data;

			//const buffer_img = res_frame.selection.data;
			//console.log(res_uint8);

			
			socket.emit('streaming',  { image: true, buffer: 'lil'}); 
		});

	});



});
*/

/*
function Uint8ToString(u8a){
  const CHUNK_SZ = 0x8000;
  const c = [];
  for (const i=0; i < u8a.length; i+=CHUNK_SZ) {
    c.push(String.fromCharCode.apply(null, u8a.subarray(i, i+CHUNK_SZ)));
  }
  return c.join("");
}
*/
app.use(express.static(__dirname + '/deep_app'))

app.get('/', function(req, res) {
	res.sendFile(appPath);
});


server.listen(serverPort, function(err){
	if (err) return console.error(err)
	console.log((new Date()) + 'DEEP Data Server is listening on https://localhost:' + serverPort);
});