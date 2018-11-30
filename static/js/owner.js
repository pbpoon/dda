var md = $('#modal1').modal();//表单框
var md2 = $('#modal2').modal();//删除提示框

//item的添加方法
function add_item(order_id) {
    $('#modal1 h6').text('添加明细行');
    var $form = $('#item_form');
    $.ajax({
        url: $form.attr('action'),
        data: {'order_id': order_id},
        method: 'GET',
        success: function (data) {
            $('#modal1 .container').html(data);
            md.modal('open')
        }
    })
}

//item的编辑方法
function edit_item(val, url) {
    $('#modal1 h6').text('修改明细行');
    $('#item_form').attr('action', url);
    $.ajax({
        method: 'GET',
        url: url,
        data: {item_id: val},
        success: function (data) {
            $('#modal1 .container').html(data);
            md.modal('open')
        }
    });
}

//把item的输入form的submit方法改成ajax
$('#item_form').on('submit', function (e) {
    var $form = $('#item_form');
    $.ajax({
        url: $form.attr('action'),
        method: 'POST',
        data: $form.serialize(),
        success: function (data) {
            if (data['status'] == 'SUCCESS') {
                md.modal('close');
                window.location.reload()
            }
            else {
                $('#modal1 .container').html(data);
                md.modal('open')
            }
        }
    });
    return false

})

// 确认删除对话框
function item_remove(item_id, url_string) {
    //添加"确认"按钮，并绑定删除的方法
    $('#modal2 p').text('确认删除该明细行?')
    var url = url_string.replace('9999', item_id);
    $('#confirm_btn').on('click', function (e) {
        delete_item(url)
    });
    md2.modal('open');
}

//删除item的方法，调用post方法
//为解决csrf token的问题而使用页面form来完成
function delete_item(url) {
    var $form = $('#post_form')
    $form.attr('action', url)
    $form.submit()
}


//post方法，日后可以用来发送post请求，原理是创建一个form，来post的方式请求
//调用方法 如：
// post('pages/statisticsJsp/excel.action',{html:prnhtml,cm1:'sdsddsd',cm2:'haha'});
function post(URL, PARAMS) {
    var temp = document.createElement("form");
    temp.action = URL;
    temp.method = "post";
    temp.style.display = "none";
    for (var x in PARAMS) {
        var opt = document.createElement("textarea");
        opt.name = x;
        opt.value = PARAMS[x];
        // alert(opt.name)
        temp.appendChild(opt);
    }
    document.body.appendChild(temp);
    temp.submit();
    return temp;
}

//onchange事件通用方法，第一参数默认是this.value，第二个参数必须为url地址，之后的参数问问input的name
function onchange_set_product_info() {
    var args = new Array(arguments.length);
    for (var i = 0; i < arguments.length; i++) {
        args[i] = arguments[i];
    }
    var DATA;
    $.ajax({
            url: arguments[1],
            method: 'GET',
            data: {'value': arguments[0]},
            success: function (data) {
                DATA = data;
                for (var i = 2; i < args.length; i++) {
                    $('#item_form [name=' + args[i] + ']').val(DATA[args[i]])
                }
            }
        }
    );

}

function onchange_set_product_list(url, kwargs) {
    $.ajax({
            url: url,
            method: 'GET',
            data: kwargs,
            success: function (data) {
                var sel = $('#item_form select[name=product]');
                sel.html("");
                sel.append("<option selected value>---------</option>");
                for (var i = 0; i < data.length; i++) {
                    sel.append("<option value='" + data[i].id + "'>" + data[i].name + data[i].type + "</option>");
                }
                $('select[name=product]').formSelect();
            }
        }
    );
}

function add_produce_item(order_id, raw_item_id) {
    var $form = $('#item_form');
    var old_action = $form.attr('action');
    $('#modal1 h6').text('添加明细行');
    md.modal({
        onCloseStart: function () {
            $form.attr('action', old_action)
        }
    });

    $form.attr('action', '{% url "kes_order_produce_item_edit" %}');
    $.ajax({
        url: $form.attr('action'),
        data: {
            'order_id': order_id,
            'raw_item_id': raw_item_id
        },
        method: 'GET',
        success: function (data) {
            $('#modal1 .container').html(data);
            md.modal('open')
        }
    })
}