define(['knockout', "jquery"], function(ko, $) {
    let headerViewModel = function(params) {
        let self = this;
        self.headerTitle = ko.observable('Web Scrapper');
        self.menuItems = ko.observableArray([
            {name: 'Home', url: 'pages/index.html'},
            {name: 'Media', url: 'pages/media.html'},
            {name: 'Websites', url: 'pages/websites.html'},
            {name: 'Scan', url: 'pages/scan.html'},
            {name: 'Settings', url: 'pages/settings.html'},
        ]);
        self.activeMenuItem = ko.observable('');
        self.useAjax = ko.observable(false);

        self.fetchDynamicContent = function(url) {
            if (self.useAjax()) {
                $.get(url, function(data) {
                    $("#content").html(data);
                });
            }
        };
    }
    
    return headerViewModel;
});
