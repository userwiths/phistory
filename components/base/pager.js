define(['knockout', "jquery"], function(ko, $) {
    let pagerViewModel = function(params) {
        let self = this;

        self.page = ko.observable(0);
        self.limit = ko.observable(10);
        self.total = ko.observable(0);
        self.pages = ko.observable(0);
        self.dir = ko.observable('asc');
        self.sort = ko.observable('date');

        self.updateTable = function() {};

        self.selectedSort = function(sort) {
            if (self.sort() === sort) {
                self.dir(self.dir() === 'asc' ? 'desc' : 'asc');
            } else {
                self.sort(sort);
                self.dir('asc');
            }
            let element = $("th." + sort);
            $("th.sortable span").remove();
            if(self.dir() === 'asc') {
                element.append('<span>&#x25B2;</span>');
            } else {
                element.append('<span>&#x25BC;</span>');
            }
            self.updateTable();
        }
        
        self.page.subscribe(function() {
            if(self.page() < 0) {
                self.page(0);
            }
            if(self.page() > self.pages()) {
                self.page(self.pages());
            }
            self.updateTable();
        });
        self.limit.subscribe(function() {
            self.updateTable();
        });
    }
    
    return pagerViewModel;
});
