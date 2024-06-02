define(['knockout', "jquery", "pager"], function(ko, $, pager) {
    let tableViewModel = function(params) {
        let self = this;
        
        self.websites = ko.observableArray();
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

        self.updateTable = function() {
            let url = self.update_url();
            url += '?';
            url += 'page=' + self.pager.page();
            url += '&limit=' + self.pager.limit();
            url += '&dir=' + self.pager.dir();
            url += '&sort=' + self.pager.sort();
            $.get(url, function(data) {
                let paging = data.paging;
                self.pager.websites(data.data);
                self.pager.total(paging.total);
                self.pager.pages(Math.ceil(paging.total / paging.limit));
            });
        };
        pager.updateTable = self.updateTable;
        self.selectedSort = pager.selectedSort;

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
        
        self.only_visited.subscribe(function() {
            if(self.pager.page() > 0) {
                self.pager.page(0);
            } else {
                self.updateTable();
            }
        });
        self.updateTable();

        //Bugs the visited only.
        //ko.cleanNode(document.getElementById(self.component_id));
        //ko.applyBindings(self, document.getElementById(self.component_id));
    }
    
    return tableViewModel;
});
