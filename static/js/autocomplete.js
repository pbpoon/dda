function set_product(val) {
    $('input[name=product]').val(val)
    $.ajax({
        url: '/product/product_info/',
        method: 'GET',
        data: {'product': val},
        success: function (data) {
            $('input[name=piece]').val(data['piece']);
            $('input[name=quantity]').val(data['quantity']);
        }
    })
}


var DATA;//用来保存get到的数据
// 实例化autocomplete组件
var $ap = $('.autocomplete').autocomplete({
    onAutocomplete: function (input) {
        // alert("aa" + DATA[input]['id'] + input);

        set_product(DATA[input]['id'])
    },
    activeIndex: function (i) {
        alert(i)

    }

});

function get_autocomplete(url) {
    var $form = $('#item_form');

    $.ajax({
        url: url,
        data: $form.serialize(),
        method: 'POST',
        success: function (data) {
            $ap.autocomplete("updateData", data);
            $ap.autocomplete("open");
            DATA = data
        }
    })
}