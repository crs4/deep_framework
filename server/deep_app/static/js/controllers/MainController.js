'use strict';
var angular = require('../../node_modules/@bower_components/angular')
angular
     .module('app')
     .controller('MainController', [
       'navService', 'eventService','dataService','$mdDialog', '$mdSidenav', '$mdBottomSheet', '$log', '$q', '$state', '$mdToast', '$scope',
        MainController
     ]);

function MainController(navService, eventService, dataService, $mdDialog, $mdSidenav, $mdBottomSheet, $log, $q, $state, $mdToast,$scope) {
  console.log('main controller');
  var vm = this;
  
  vm.menuItems = [ ];
  vm.selectItem = selectItem;
  vm.toggleItemsList = toggleItemsList;
  vm.showActions = showActions;
  vm.title = $state.current.data.title;
  vm.showSimpleToast = showSimpleToast;
  vm.toggleRightSidebar = toggleRightSidebar;

  vm.status = dataService.getStatus()
  var initialPoll = setInterval(() => {
    vm.status = dataService.getStatus()
    $scope.$apply()
    // console.log('Status: ' + vm.status)
  }, 300)

  eventService.get_data(function(event) {
      var result_event = (event.data);
      
      console.log(result_event);
      $mdDialog.show(
        $mdDialog.alert()
          .parent(angular.element(document.querySelector('#popupContainer')))
          .clickOutsideToClose(true)
          .title('Event')
          .textContent(result_event)
          .ariaLabel('Alert Dialog Demo')
          .ok('Got it!')
      );
      setTimeout(function(){ $mdDialog.hide() }, 2000);
  });


  navService
    .loadAllItems()
    .then(function(menuItems) {
      vm.menuItems = [].concat(menuItems);
    });

  function toggleRightSidebar() {
      $mdSidenav('right').toggle();
  }

  function toggleItemsList() {
    var pending = $mdBottomSheet.hide() || $q.when(true);

    pending.then(function(){
      $mdSidenav('left').toggle();
    });
  }

  function selectItem (item) {
    vm.title = item.name;
    vm.toggleItemsList();
    vm.showSimpleToast(vm.title);
  }

  

  function showActions($event) {
      $mdBottomSheet.show({
        parent: angular.element(document.getElementById('content')),
        templateUrl: 'static/js/views/partials/records.html',
        controller: 'RecordController',
        scope: $scope,
        preserveScope: true
        //targetEvent: $event
      }).then(function(clickedItem) {
        clickedItem && $log.debug( clickedItem.name + ' clicked!');
      });
      
  }

  function showSimpleToast(title) {
    $mdToast.show(
      $mdToast.simple()
        .content(title)
        .hideDelay(2000)
        .position('bottom right')
    );
  }

  vm.docsUrl = `https://${location.hostname}:8000/api/docs`
}
