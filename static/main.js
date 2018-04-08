(function() {
  "use strict";

  angular
    .module("WordcountApp", [])

    .controller("WordcountController", [
      "$scope",
      "$log",
      "$http",
      "$timeout",
      function($scope, $log, $http, $timeout) {
        $scope.submitButtonText = "Submit";
        $scope.loading = false;
        $scope.urlerror = false;
        $scope.getResults = function() {
          // get the URL from the input
          var userInput = $scope.url;

          // fire the API request
          $http
            .post("/start", { url: userInput })
            .success(function(results) {
              $scope.urlerror = false;
              getWordCount(results);
              $scope.wordcounts = null;
              $scope.loading = true;
              $scope.submitButtonText = "Loading...";
            })
            .error(function(error) {
              $log.log(error);
            });
        };

        function getWordCount(jobID) {
          var timeout = "";

          var poller = function() {
            // fire another request
            $http
              .get("/results/" + jobID)
              .success(function(data, status, headers, config) {
                if (status === 202) {
                  $log.log(data, status);
                } else if (status === 200) {
                  $scope.loading = false;
                  $scope.submitButtonText = "Submit";
                  $scope.wordcounts = data;
                  $timeout.cancel(timeout);
                  return false;
                }
                // continue to call the poller() function every 2 seconds
                // until the timeout is cancelled
                timeout = $timeout(poller, 2000);
              })
              .error(function(error) {
                $log.log(error);
                $scope.loading = false;
                $scope.submitButtonText = "Submit";
                $scope.urlerror = true;
              });
          };
          poller();
        }
      }
    ])
    .directive("wordCountChart", [
      "$parse",
      function($parse) {
        return {
          // restrictive to html element
          restrict: "E",
          // replace directive with HTML in template
          replace: true,
          template: '<div id="chart"></div>',
          // gives access to scope variables in the controller
          link: function(scope) {
            scope.$watch(
              "wordcounts",
              function() {
                d3
                  .select("#chart")
                  .selectAll("*")
                  .remove();
                var data = scope.wordcounts;
                for (var word in data) {
                  if (word < data.length-1){
                    console.log(word)
                    d3
                    .select("#chart")
                    .append("div")
                    .selectAll("div")
                    .data(word)
                    .enter()
                    .append("div")
                    .style("width", function() {
                      return data[word][1]/data[data.length-1] * 1000 + "px";
                    })
                    .text(function(d) {
                      return data[word][0];
                    });
                  }
                }
              },
              true
            );
          }
        };
      }
    ]);
})();
