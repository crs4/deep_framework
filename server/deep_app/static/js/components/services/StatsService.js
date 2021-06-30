'use strict';
var angular = require('../../../node_modules/@bower_components/angular')
angular.module('app')
      .service('statsService', [
    statsService
]);

function statsService(){
  var data = {}
  var stats_source = new EventSource('/api/stats')
  var stats_data = {}
  var sources = []
  var pipelines = []
  var selected_source = undefined
  var selected_pipeline = undefined
  stats_source.addEventListener("message", (message) => {
    var temp_j = (message.data).replace(/'/g, '"');
    stats_data = JSON.parse(temp_j)
    //console.log($scope.stats_data,'out');
    sources = Object.keys(stats_data)
    if (sources.length == 0) {
      selected_source = undefined
      return
    }
    if (selected_source == undefined) {
      selected_source = sources[0]
    }
    let pipelines_data = stats_data[selected_source].pipelines
    pipelines = Object.keys(pipelines_data)
    if (pipelines.length == 0) {
      selected_pipeline = undefined
      return
    }
    if (selected_pipeline == undefined) {
      selected_pipeline = pipelines[0]
    }
  }, false)
  return {
    get_data: function(callback) {
      stats_source.addEventListener("message", callback, false);
    },
    set_selected_source: function(s) {
      if (s ==  selected_source) return
      selected_source = s
      let pipelines_data = stats_data[selected_source].pipelines
      pipelines = Object.keys(pipelines_data)
      if (pipelines.length == 0) {
        selected_pipeline = undefined
        return
      }
      selected_pipeline = pipelines[0]
    },
    get_selected_source: function() {
      return selected_source
    },
    set_selected_pipeline: function (s) {
      if (s == selected_pipeline) return
      selected_pipeline = s
    },
    get_selected_pipeline: function () {
      return selected_pipeline
    },
    get_sources: function () {
      return sources
    },
    get_pipelines: function () {
      return pipelines
    }
  }; 
  


}
