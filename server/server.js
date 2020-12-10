
const monitor_address = process.env.MONITOR_ADDRESS || '0.0.0.0'
const monitor_port = process.env.MONITOR_STATS_OUT || '3000'
const algs = process.env.ALGS

const collector_ports = process.env.COLLECTOR_PORTS
const collector_port_arr = collector_ports.split(",");

const stream_man_pair_ports = process.env.STREAM_MANAGER_PAIR_PORTS
const stream_man_pair_ports_arr = stream_man_pair_ports.split(",");

const protocol = process.env.PROT || 'tcp://'

const appPath = process.cwd() + '/deep_app/static/index.html' // '/home/deepframework/server/deep_app/templates/index.html'
const serverPort = process.env.SERVER_PORT || 8000

const express  = require('express');
const app = express();
const https = require("https")
const fs = require("fs")

const swaggerUi = require('swagger-ui-express');
const swagger_file_path = process.cwd() + '/swagger.json';
var swaggerDoc = require.resolve(swagger_file_path);

const server = https.createServer({
	key: fs.readFileSync('./cert/key.pem'),
	cert: fs.readFileSync('./cert/cert.pem'),
	// ca: fs.readFileSync('./cert/ca.cert.pem')
}, app);

const apis_list = [];
const apis_map = [];

/**
 * Hyperpeer server
 */
const HpServer = require('hyperpeer-node');
const verifyPeer = function (type, peerId, peerKey) {
	return true;
}
const hpServer = new HpServer({ server: server, verifyPeer: verifyPeer });

const zmq = require('zeromq');

const monitor_sock = zmq.socket('sub');


monitor_sock.connect(protocol + monitor_address + ':' + monitor_port);
monitor_sock.subscribe('');

var stream_man_sock_list = [];
for (var i = 0; i < stream_man_pair_ports_arr.length; i++) {

	var stream_man = stream_man_pair_ports_arr[i];
	var stream_man_split = stream_man.split(":");
	const source_id = stream_man_split[0];
	var stream_man_pair_port = stream_man_split[1];
	const stream_man_pair_sock = zmq.socket('pair');
	stream_man_pair_sock.bind(protocol +'*:'+ stream_man_pair_port);
	stream_man_sock_list.push(stream_man_pair_sock)

	app.post('/api/stream_'+source_id+'/start', function(request, response){

		stream_man_pair_sock.send('START');
		return response.send(source_id+ ' started');


	});

	app.post('/api/stream_'+source_id+'/stop', function(request, response){
		stream_man_pair_sock.send('STOP');
		return response.send(source_id+ ' stopped');
	});
};
	




var source_id_list = []

for (var i = 0; i < collector_port_arr.length; i++) {

	col_name_port = collector_port_arr[i];
	col_split = col_name_port.split(":");
	det_name = col_split[0];
	source_id = col_split[1];
	source_id_list.push(source_id);
	col_port = col_split[2]

	const col_sock = zmq.socket('pair');
	col_sock.bind(protocol +'*:'+ col_port);

	app.get('/api/stream_'+source_id+'/'+det_name, function(request, response){

		response.writeHead(200, {
		'Content-Type': 'text/event-stream',
		'Cache-Control': 'no-cache',
		'Connection': 'keep-alive'
		});

		col_sock.on("message", function(data) {
			response.write("data: " + data.toString() + "\n\n");
		});
	});
}

app.post('/api/start', function(request, response){
	for (var i = 0; i < stream_man_sock_list.length; i++) {
		var sock = stream_man_sock_list[i];
		sock.send('START');
	};	
	return response.send('All sources started');


});

app.post('/api/stop', function(request, response){
	for (var i = 0; i < stream_man_sock_list.length; i++) {
		var sock = stream_man_sock_list[i];
		sock.send('STOP');
	};
	return response.send('All sources stopped');
});


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




app.use(express.static(__dirname + '/deep_app'))

app.get('/', function(req, res) {
	res.sendFile(appPath);
});

app.get('/swagger.json', function(req, res) {
	res.setHeader("Access-Control-Allow-Origin", "*");
	res.sendFile(swagger_file_path);
});


app._router.stack.forEach(function(r){
  if (r.route && r.route.path){
    apis_list.push(r.route.path)
  }
})

const apis_map_dict = create_api_map(apis_list,source_id_list);
write_apis_file(apis_map_dict);
var options = {
  swaggerOptions: {
    url: 'https://localhost:8000/swagger.json'
  }
}
// app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(null,options));

// app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(swaggerDoc));
app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(apis_map_dict));

server.listen(serverPort, function(err){
	if (err) return console.error(err)
	console.log((new Date()) + 'DEEP Data Server is listening on https://localhost:' + serverPort);
});



function create_api_map(endpoints_list,source_id_list) {

	var tags = [];
	for (var i = 0; i < source_id_list.length; i++) {
		console.log(source_id_list[i]);
		var source_tag = {"name": "Source_"+source_id_list[i],"description": "List of api available for source with ID "+source_id_list[i]};
		tags.push(source_tag);
	}
	tags.push({"name":"pipeline_info","description":"information and statistics about pipeline execution"});
	tags.push({"name":"pipeline_operations","description":"List of operation available on pipeline"});
	const apis_map = {
		"swagger":"2.0",
		"info": {
			"version": "1.0.0",
			"title": "DeepFramework APIs",
			"license": {
				"name": "MIT"
			}
		},
		"tags":tags,

		"paths": {}
		

	};
  	var responses = {"200":{"description": "Successful operation"},"400":{"description": "Invalid status value"}};
	
	for (var i = 0; i < endpoints_list.length; i++) {
		end_p = endpoints_list[i];


		
		if (end_p == '/api/algs'){
			produces = ['application/json'];
			info = {"get": { "summary": "List all descriptors","tags":["pipeline_info"],"responses":responses,"produces":produces}};
			apis_map['paths'][end_p] = info;
			continue
		}
		if (end_p == '/api/stats'){
			produces = ['application/json'];
			info = {"get": { "summary": "List all component statistics","tags":["pipeline_info"],"responses":responses,"produces":produces}};
			apis_map['paths'][end_p] = info;
			continue
		}
		if (end_p == '/api/start'){
			produces = ['application/json'];
			info = {"post": { "summary": "Start all sources","tags":["pipeline_operations"],"responses":responses,"produces":produces}};
			apis_map['paths'][end_p] = info;
			continue
		}
		if (end_p == '/api/stop'){
			produces = ['application/json'];
			info = {"post": { "summary": "Stop all sources","tags":["pipeline_operations"],"responses":responses,"produces":produces}};
			apis_map['paths'][end_p] = info;
			continue
		}
		if (end_p.includes('stream')){

			end_p_split = end_p.split("/");
			stream_id = end_p_split[2].split('_')[1];
			spec = end_p_split[3];
			

			if (end_p.includes('start') || end_p.includes('stop')){
				var summary = `It sends ${spec} signal to the source with ID ${stream_id}`;
				var produces = ['application/json'];
				var info = {"post": { "summary": summary, "responses":responses,"tags":["Source_"+stream_id],"produces":produces}};

			}
			else {
				var summary = `List results for source with ID ${stream_id} analyzed by the detector with CATEGORY ${spec}`;
				var produces = ['text/event-stream'];
				var info = {"get": { "summary": summary, "responses":responses,"tags":["Source_"+stream_id],"produces":produces}};

			}
			apis_map['paths'][end_p] = info;
		}
	}
	return apis_map
		

}

function write_apis_file(data_apis){
	const data_apis_json = JSON.stringify(data_apis);
	//console.log(data_apis_json);


	// write file to disk
	fs.writeFile(swagger_file_path, data_apis_json, 'utf8', (err) => {

	    if (err) {
	        console.log(`Error writing file: ${err}`);
	    };

	});
}

