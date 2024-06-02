requirejs.config({
    baseUrl: '/',
    paths: {
        text: 'https://cdnjs.cloudflare.com/ajax/libs/require-text/2.0.12/text.min',
        jquery: 'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.5.1/jquery.min',
        knockout: 'https://cdnjs.cloudflare.com/ajax/libs/knockout/3.5.0/knockout-min',
        pager: 'components/base/pager'
    }
});
requirejs(["knockout", "jquery"], function(ko, $) {
    ko.components.register(
        "website-table",
        {
            viewModel : {require: "components/websites/table"},
            template: {require: "text!components/websites/table.html"}
        }
    );
    ko.components.register(
        "visit-table",
        {
            viewModel : {require: "components/visits/table"},
            template: {require: "text!components/visits/table.html"}
        }
    );
    ko.components.register(
        "header-component",
        {
            viewModel : {require: "components/layout/header"},
            template: {require: "text!components/layout/header.html"}
        }
    );
    ko.components.register(
        "media-table",
        {
            viewModel : {require: "components/media/table"},
            template: {require: "text!components/media/table.html"}
        }
    );
    ko.components.register(
        "base-table",
        {
            viewModel : {require: "components/base/table"},
            template: {require: "text!components/base/table.html"}
        }
    );
    ko.components.register(
        "pager",
        {
            viewModel : {require: "components/base/pager"},
            template: {require: "text!components/base/pager.html"}
        }
    );
    ko.applyBindings();
});