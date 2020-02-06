
'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
	.module('app')
	.controller('RecordController', [
		'$scope',
		'$interval',
		'algService',
		'statsService',
		'FileSaver',
		'Blob',
		RecordController
	]);

function RecordController($scope,$interval,algService,statsService,FileSaver,Blob) {

	
	console.log('prime');

	$scope.startRecording = function(){
		init();
		console.log('dentro');
		$scope.timer_count = $interval(timer_inc, 1000);
		
		statsService.get_data(function(response) {
			var temp_j = (response.data).replace(/'/g, '"');
			var data = JSON.parse(temp_j);
			$scope.fps_data['VideoCapture'].push(data.VideoCapture['fps'])
			$scope.fps_data['Collector'].push(data.Collector['fps'])
			$scope.fps_data['FrameProvider'].push(data.FrameProvider['fps'])
			angular.forEach(data['algorithms'], function(value, key) {
				if (Object.keys($scope.fps_data).indexOf(key) > 0){
					$scope.fps_data[key].push(value['fps']);
				}
			});

		
		
		});



	}

	$scope.stopRecording = function(){
		$scope.timerRunning = false;
		$interval.cancel($scope.timer_count);
		console.log('stops');
		//console.log($scope.fps_data);
		angular.forEach($scope.fps_data, function(value, key) {
			var sum = value.reduce((a, b) => a + b, 0);
			$scope.mean_fps_data[key] = sum / (value.length);
		});
		$scope.table_visible = true;
		//console.log($scope.mean_fps_data);
	}

	function init(){

		$scope.fps_data = {};
		$scope.mean_fps_data = {};
		$scope.table_visible = false;
		$scope.timerRunning = true;
		$scope.seconds = 0;
		$scope.fps_data['VideoCapture'] = [];
		$scope.fps_data['Collector'] = [];
		$scope.fps_data['FrameProvider'] = [];



		algService.get_algs().then(function(data){
			for (var i = 0; i < data.algs_list.length; i++) {
				
				$scope.fps_data[data.algs_list[i]] = [];
			};
		});

	}

	$scope.download = function(){

		var data_to_write = $scope.mean_fps_data;
		data_to_write['time_elapsed'] = $scope.seconds;
		text = JSON.stringify(data_to_write);
		var data = new Blob([text], { type: 'text/plain;charset=utf-8' });
		var now = new Date();
		FileSaver.saveAs(data, 'stats'+now+'.txt');
	}

	function timer_inc(){
		$scope.seconds = $scope.seconds+1;
	}

	

	$scope.showTable = function(){
		$scope.table_visible = true;
	}

	$scope.hideTable = function(){
		$scope.table_visible = false;
	}

}
