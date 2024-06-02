define(['knockout', "jquery"], function(ko, $) {
    let tableViewModel = function(params) {
        let self = this;
        
        self.headerColumns = ko.observableArray([]);
        self.contentColumns = ko.observableArray([]);
        self.items = ko.observableArray([]);

        self.page = ko.observable(0);
        self.limit = ko.observable(10);
        self.total = ko.observable(0);
        self.pages = ko.observable(0);
        self.dir = ko.observable('asc');
        self.sort = ko.observable('date');

        self.update_url = 'http://localhost:8000/media'
        self.component_id = "component-wrapper";

        let updateTable = function() {
            let url = self.update_url;
            url += '?';
            url += 'page=' + self.page();
            url += '&limit=' + self.limit();
            url += '&dir=' + self.dir();
            url += '&sort=' + self.sort();
            $.get(url, function(data) {
                let paging = data.paging;
                self.visits(data.data);
                self.total(paging.total);
                self.pages(Math.ceil(paging.total / paging.limit));
            });
        };
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
            updateTable();
        }

        
        self.visit_id.subscribe(function() {
            self.getDetails();
        });
        self.closeModal = function() {
            self.modal_visible(false);
        };
        self.setId = function(visit) {
            let id = visit.visit_id;
            self.visit_id(id);
        };
        
        self.page.subscribe(function() {
            if(self.page() < 0) {
                self.page(0);
            }
            if(self.page() > self.pages()) {
                self.page(self.pages());
            }
            updateTable();
        });
        self.limit.subscribe(function() {
            updateTable();
        });
        updateTable();
    }
    
    return tableViewModel;
});
