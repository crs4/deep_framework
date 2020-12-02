
const monitor_address = process.env.MONITOR_ADDRESS || '0.0.0.0'
const monitor_port = process.env.MONITOR_STATS_OUT || '3000'
const algs = process.env.ALGS

const collector_ports = process.env.COLLECTOR_PORTS
const collector_port_arr = collector_ports.split(",");

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




for (var i = 0; i < collector_port_arr.length; i++) {

	col_name_port = collector_port_arr[i];
	col_split = col_name_port.split(":");
	det_name = col_split[0];
	source_id = col_split[1];
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

const apis_map_dict = create_api_map(apis_list);
write_apis_file(apis_map_dict);
var options = {
  swaggerOptions: {
    url: 'https://localhost:8000/swagger.json'
  }
}
app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(null,options));

//app.use('/api/docs', swaggerUi.serve, swaggerUi.setup(swaggerDoc));

server.listen(serverPort, function(err){
	if (err) return console.error(err)
	console.log((new Date()) + 'DEEP Data Server is listening on https://localhost:' + serverPort);
});

function create_api_map(endpoints_list) {
	
	const apis_map = {
		"swagger":"2.0",
		"info": {
			"version": "1.0.0",
			"title": "DeepFramework APIs",
			"license": {
				"name": "MIT"
			}
		},
		"tags":[{"name":"results","description":"results of source information extraction"},{"name":"pipeline_info","description":"information and statistics about pipeline execution"}],

		"paths": {}
		

	};
  	responses = {"200":{"description": "Successful operation"},"400":{"description": "Invalid status value"}};
	produces = ['text/event-stream'];
	for (var i = 0; i < endpoints_list.length; i++) {
		end_p = endpoints_list[i];


		
		if (end_p == '/api/algs'){
			info = {"get": { "summary": "List all descriptors","tags":["pipeline_info"],"responses":responses,"produces":produces}};
			apis_map['paths'][end_p] = info;
			continue
		}
		if (end_p == '/api/stats'){
			info = {"get": { "summary": "List all component statistics","tags":["pipeline_info"],"responses":responses,"produces":produces}};
			apis_map['paths'][end_p] = info;
			continue
		}
		if (end_p.includes('stream')){
			end_p_split = end_p.split("/");
			
			stream_id = end_p_split[2].split('_')[1];
			det_name = end_p_split[3];
			summary = `List results for source ${stream_id} analyzed with detector ${det_name}`;
			responses = {"200":{"description": "successful operation"},"400":{"description": "Invalid status value"}};
			info = {"get": { "summary": summary, "responses":responses,"tags":["results"],"produces":produces}};
			apis_map['paths'][end_p] = info;
		}
	}
	return apis_map
		

}

function write_apis_file(data_apis){
	const data_apis_json = JSON.stringify(data_apis);
	console.log(data_apis_json);


	// write file to disk
	fs.writeFile(swagger_file_path, data_apis_json, 'utf8', (err) => {

	    if (err) {
	        console.log(`Error writing file: ${err}`);
	    } else {
	        console.log(`File is written successfully!`);
	    }

	});
}

