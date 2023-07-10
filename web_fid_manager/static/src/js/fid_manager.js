/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
var FidManagerWidget = Widget.extend({
   template: 'FidManagerSystray',
   events: {
       'click #open_fid_manager': '_onClick',
   },
   _onClick: function(){
       this.do_action({
            type: 'ir.actions.act_url',
            target: 'new',
            url: 'https://blue-rock.fid-manager.be/fr/Job#/job/1/33/2021/3',
       });
   },
});
SystrayMenu.Items.push(FidManagerWidget);
export default FidManagerWidget;