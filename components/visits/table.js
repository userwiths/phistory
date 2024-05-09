define(['knockout', "jquery"], function(ko, $) {
    let tableViewModel = function(params) {
        let self = this;
        
        self.visits = ko.observableArray();
        self.page = ko.observable(0);
        self.limit = ko.observable(10);
        self.total = ko.observable(0);
        self.pages = ko.observable(0);
        self.dir = ko.observable('asc');
        self.sort = ko.observable('url');
        self.visit_id = ko.observable(0);
        self.update_url = 'http://localhost:8000/visits'

        //modal
        self.modal_visible = ko.observable(false);
        self.details = ko.observable({});
        self.image = ko.observable('');
        self.title = ko.observable('');
        self.description = ko.observable('');

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

        self.getImage = function() {
            let image = "";
            let accepted = ["og:image", "twitter:image", "image"];
            if (self.visit_id() == 0 || !self.modal_visible()) {
                return image;
            }
            self.details().metadata.forEach(function(item){
                if (accepted.includes(item.identifier_name)) {
                    image = item.attribute_value;
                }
                if(accepted.includes(item.attribute_value)) {
                    image = item.identifier_name;
                }
            });
            if (image.startsWith("/") ) {
                image = self.details().url + image;
            }
            if(!image.includes("www.") && image.includes("google")) {
                image = image.split("//");
                image = image[0] + "//www." + image[1];
            }
            return image;
        }
        self.getTitle = function() {
            let title = "";
            let accepted = ["og:title", "twitter:title", "title"];
            if (self.visit_id() == 0 || !self.modal_visible()) {
                return title;
            }
            self.details().metadata.forEach(function(item){
                if (accepted.includes(item.identifier_name)) {
                    title = item.attribute_value;
                }
                if (accepted.includes(item.identifier)) {
                    title = item.identifier_name;
                }
                if(accepted.includes(item.attribute_value)) {
                    title = item.identifier_name;
                }
            });
            return title;
        };
        self.getDescription = function() {
            let description = "";
            let accepted = ["og:description", "twitter:description", "description"];
            if (self.visit_id() == 0 || !self.modal_visible()) {
                return description;
            }
            self.details().metadata.forEach(function(item){
                if (accepted.includes(item.identifier_name)) {
                    description = item.attribute_value;
                }
                if (accepted.includes(item.identifier)) {
                    description = item.identifier_name;
                }
                if(accepted.includes(item.attribute_value)) {
                    description = item.identifier_name;
                }
            });
            return description;
        };
        self.getDetails = function() {
            $.get('http://localhost:8000/visits/' + self.visit_id(), function(data) {
                self.details(data);
                self.image(self.getImage());
                self.title(self.getTitle());
                self.description(self.getDescription());
                self.modal_visible(true);
            });
        };
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
