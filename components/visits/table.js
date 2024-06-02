define(['knockout', "jquery", "pager"], function(ko, $, pager) {
    let tableViewModel = function(params) {
        let self = this;
        
        self.pager = new pager();
        self.pager.sort('url');

        self.visits = ko.observableArray();
        self.visit_id = ko.observable(0);
        self.update_url = 'http://localhost:8000/visits'

        //modal
        self.modal_visible = ko.observable(false);
        self.details = ko.observable({});
        self.image = ko.observable('');
        self.title = ko.observable('');
        self.description = ko.observable('');

        self.component_id = "component-wrapper";

        self.updateTable = function() {
            let url = self.update_url;
            url += '?';
            url += 'page=' + self.pager.page();
            url += '&limit=' + self.pager.limit();
            url += '&dir=' + self.pager.dir();
            url += '&sort=' + self.pager.sort();
            $.get(url, function(data) {
                let paging = data.paging;
                self.visits(data.data);
                self.pager.total(paging.total);
                self.pager.pages(Math.ceil(paging.total / paging.limit));
            });
        };
        self.pager.updateTable = self.updateTable;
       
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
        
        
        self.updateTable();
    }
    
    return tableViewModel;
});
