define(['knockout', "jquery"], function(ko, $) {
    let tableViewModel = function(params) {
        let self = this;
        
        self.websites = ko.observableArray();
        self.page = ko.observable(0);
        self.limit = ko.observable(10);
        self.total = ko.observable(0);
        self.pages = ko.observable(0);
        self.dir = ko.observable('asc');
        self.sort = ko.observable('url');
        self.only_visited = ko.observable(false);
        self.website_id = ko.observable();
        self.update_url = ko.computed(function() {
            if (self.only_visited()) {
                return 'http://localhost:8000/visits/actual';
            } else {
                return 'http://localhost:8000/visits';
            }
        });

        //modal
        self.modal_visible = ko.observable(false);
        self.website_details = ko.observable({});
        self.website_image = ko.observable('');
        self.website_title = ko.observable('');
        self.website_description = ko.observable('');

        self.component_id = "component-wrapper";

        let updateTable = function() {
            let url = self.update_url();
            url += '?';
            url += 'page=' + self.page();
            url += '&limit=' + self.limit();
            url += '&dir=' + self.dir();
            url += '&sort=' + self.sort();
            $.get(url, function(data) {
                let paging = data.paging;
                self.websites(data.data);
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

        self.getWebsiteImage = function() {
            let image = "";
            let accepted = ["og:image", "twitter:image", "image"];
            if (self.website_id() == 0 || !self.modal_visible()) {
                return image;
            }
            self.website_details().metadata.forEach(function(item){
                if (accepted.includes(item.identifier_name)) {
                    image = item.attribute_value;
                }
                if(accepted.includes(item.attribute_value)) {
                    image = item.identifier_name;
                }
            });
            if (image.startsWith("/") ) {
                image = self.website_details().url + image;
            }
            if(!image.includes("www.") && image.includes("google")) {
                image = image.split("//");
                image = image[0] + "//www." + image[1];
            }
            return image;
        }
        self.getWebsiteTitle = function() {
            let title = "";
            let accepted = ["og:title", "twitter:title", "title"];
            if (self.website_id() == 0 || !self.modal_visible()) {
                return title;
            }
            self.website_details().metadata.forEach(function(item){
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
        self.getWebsiteDescription = function() {
            let description = "";
            let accepted = ["og:description", "twitter:description", "description"];
            if (self.website_id() == 0 || !self.modal_visible()) {
                return description;
            }
            self.website_details().metadata.forEach(function(item){
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
        self.getWebsiteDetails = function() {
            $.get('http://localhost:8000/visits/' + self.website_id(), function(data) {
                self.website_details(data);
                self.website_image(self.getWebsiteImage());
                self.website_title(self.getWebsiteTitle());
                self.website_description(self.getWebsiteDescription());
                self.modal_visible(true);
            });
        };
        self.website_id.subscribe(function() {
            self.getWebsiteDetails();
        });
        self.closeModal = function() {
            self.modal_visible(false);
        };
        self.setWebsiteId = function(website) {
            let id = website.website_id;
            self.website_id(id);
        };
        self.getTags = function(website) {
            let tags = "";
            website.tags.forEach(function(tag) {
                tags += tag.tag + ", ";
            });
            return tags.slice(0, -2);
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
        self.only_visited.subscribe(function() {
            if(self.page() > 0) {
                self.page(0);
            } else {
                updateTable();
            }
        });
        updateTable();

        //Bugs the visited only.
        //ko.cleanNode(document.getElementById(self.component_id));
        //ko.applyBindings(self, document.getElementById(self.component_id));
    }
    
    return tableViewModel;
});
