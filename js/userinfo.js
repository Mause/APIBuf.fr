$(document).ready(function(){
    function delete_buffr (event) {
        console.log(event);
        function process_responce(data) {
            if (data.error !== null && data.error !== 'no_such_buffr' ){
                if (data.error === 'malformed_url'){
                    console.log('Malformed url');
                } else {
                    console.log('Unknown error');
                }
            } else {
                if (data.message == 'successful' || data.error === 'no_such_buffr'){
                    console.log('Deletion successful');
                    $($(event.toElement).parents()[2]).hide(
                        "slide",
                        {"direction":"up"},
                        250);
                }
            }
        }
        $.getJSON('/ajax/buffr/delete/' + $(event.toElement).data().key,
            process_responce);
    }

    delete_buttons = $('.delete_button');
    delete_buttons.each(function(index){
        $(delete_buttons[index]).click(delete_buffr);
    });
});
