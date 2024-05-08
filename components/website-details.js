define(['knockout', "jquery"], function(ko, $) {
    let detailsViewModel = function(params) {
        let self = this;
        
        ko.cleanNode(document.getElementById(self.component_id));
        ko.applyBindings(self, document.getElementById(self.component_id));
    }  
    
    return detailsViewModel;
});
