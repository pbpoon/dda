var form_md = $('#form_modal').modal();
var md = $('#modal1').modal();//表单框
var md2 = $('#modal2').modal();//删除提示框
var md3 = $('#modal3').modal();//下面弹窗提示框
var md_package_list = $('#modal_package_list').modal();//码单弹窗提示框
var md_cart = $('#modal_cart').modal();

function add_item_modal_form(url) {
    $('#form_modal h6').text('添加明细行');
    $.ajax({
        url: url,
        method: 'GET',
        success: function (data) {
            $('#form_modal .container').html(data);
            $('#modal_form').attr('action', url);
            // when modal is open
            form_md.modal('open');
            // $('#modal1').removeAttr('tabindex');
        }
    })
}

//item的添加方法
function add_item(url) {
    $('#modal1 h6').text('添加明细行');
    $.ajax({
        url: url,
        method: 'GET',
        success: function (data) {
            $('#modal1 .container').html(data);
            $('#item_form').attr('action', url);
            // when modal is open
            md.modal('open');
            // $('#modal1').removeAttr('tabindex');
        }
    })
}

//item的编辑方法
function edit_item(url) {
    $('#modal1 h6').text('修改明细行');
    $('#item_form').attr('action', url);
    $.ajax({
        method: 'GET',
        url: url,
        success: function (data) {
            $('#modal1 .container').html(data);
            md.modal('open');
            $('#modal1').removeAttr('tabindex');
        }
    });
}


$("#item_form").on('submit', (function (ev) {
    var $form = $('#item_form');
    ev.preventDefault();
    $.ajax({
        xhr: function () {
            var progress = $('.progress'), xhr = $.ajaxSettings.xhr();

            progress.show();

            xhr.upload.onprogress = function (ev) {
                if (ev.lengthComputable) {
                    var percentComplete = parseInt((ev.loaded / ev.total) * 100);
                    progress.val(percentComplete);
                    if (percentComplete === 100) {
                        progress.hide().val(0);
                    }
                }
            };

            return xhr;
        },
        url: $form.attr('action'),
        type: 'POST',
        data: new FormData(this),
        contentType: false,
        cache: false,
        processData: false,
        beforeSend: function (XMLHttpRequest) {
            $('.progress').show;
            $("#submit").attr({disabled: "disabled"})
        },
        complete: function () {
            $("#submit").removeAttr("disabled");
        },
        success: function (data, status, xhr) {
            if (data['state'] == 'ok') {
                console.log('ok');
                md.modal('close');
                if (data['url']) {
                    location.replace(data['url'])
                } else {
                    location.reload()
                }
            }
            else {
                $('#modal1 .container').html(data);
                md.modal('open')
            }
        },
        error: function (xhr, status, error) {
            // ...
        }
    });
}));


//把item的输入form的submit方法改成ajax
// $('#item_form').on('submit', function (e) {
//     var $form = $('#item_form');
//     var form_data = new FormData($form.get(0));
//     $.ajax({
//         url: $form.attr('action'),
//         method: 'POST',
//         data: $form.serialize(),
//         success: function (data) {
//             if (data['state'] == 'ok') {
//                 console.log('ok');
//                 md.modal('close');
//                 if (data['url']) {
//                     location.replace(data['url'])
//                 } else {
//                     location.reload()
//                 }
//             }
//             else {
//                 $('#modal1 .container').html(data);
//                 md.modal('open')
//             }
//         }
//     });
//     return false
//
// });

// 确认删除对话框
function item_remove(url) {
    //添加"确认"按钮，并绑定删除的方法
    $('#modal2 p').text('确认删除该明细行?')
    // var url = url_string.replace('9999', item_id);
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

//onchange事件通用方法，第一参数默认是this，第二个参数必须为url地址，之后的参数问问input的name
function onchange_set_product_info(url) {
    var form = $('#item_form');
    $.ajax({
            url: url,
            method: 'GET',
            data: form.serialize(),
            success: function (data) {
                for (var d in data) {
                    $('#item_form [name=' + d + ']').val(data[d])
                }
                // for (var i = 2; i < args.length; i++) {
                //     $('#item_form [name=' + args[i] + ']').val(DATA[args[i]])
                // }
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

function show_package_list() {
    $.ajax({
        url: arguments[0],
        method: 'GET',
        success: function (data) {
            $('#modal3 .list').html(data);
            md3.modal('open')
        }
    })
}

function add_produce_item(url, produce_type) {
    if (produce_type == 'slab') {
        $('#choice_btn').show()
        $('#quick_create_btn').show()
        // var footer = $('#modal1 .modal-footer');
        // $('#modal1 .modal-footer').append("<button class='btn' onclick='choice_package_list()'>选取码单</button>")
    }
    var $form = $('#item_form');
    var old_action = $form.attr('action');
    $('#modal1 h6').text('添加明细行');
    md.modal({
        onCloseStart: function () {
            $form.attr('action', old_action)
        }
    });
    $form.attr('action', url);
    $.ajax({
        url: $form.attr('action'),
        method: 'GET',
        success: function (data) {
            $('#modal1 .container').html(data);
            md.modal('open')
        },
        error: function () {
            $form.attr('action', old_action)
        }
    })
}

function open_package_list(url, state) {
    $.ajax({
        url: url,
        method: 'GET',
        data: {'state': state},
        success: function (data) {
            $('#modal_package_list .modal-content').html(data);
            $('#select_slab_form').attr('action', url);
            md_package_list.modal('open');
            $('.tabs').tabs();
            sum()
            // $('#select_slab_form').attr('action', url);
        },
        error: function () {
            alert("打开遇到错误！")
        }
    });
}

function open_package_list_by_stock(url) {
    $.ajax({
        url: url,
        method: 'GET',
        success: function (data) {
            $('#modal_package_list .modal-content').html(data);
            md_package_list.modal('open');
            $('.tabs').tabs();
            sum()
            // $('#select_slab_form').attr('action', url);
        },
        error: function () {
            alert("打开遇到错误！")
        }
    });
}

//!码单package_list页面

function sum() {
    var display = "";
    var m2 = Number(0);
    var piece = 0;
    $('input[name=select]').each(function (e) {
        var $input = $(this);
        if (this.checked) {
            console.log($input.data('quantity'), $input.val());
            m2 += Number($input.data('quantity'));
            piece += 1
        }
    });
    display = "<span>选择了：" + piece + "件 / " + Math.round(m2 * 100) / 100 + "m2</span>";
    $('#select_display').html(display)
}


function show_car_detail() {
    $.ajax({
        url: arguments[0],
        method: 'GET',
        success: function (data) {
            $('#modal_cart .list').html(data);
            md_cart.modal('open')
        }
    })
}

//库存盘点添加item设置block
function set_block(val) {
    $('input[name=block]').val(val);
}

//对应public.views的confirm
function confirm_option(url) {
    $.ajax({
        url: url,
        method: 'GET',
        success: function (data) {
            $('#modal1 .container').html(data);
            $('#item_form').attr('action', url);
            md.modal('open')
        }
    })
}

$("#modal_form").on('submit', (function (ev) {
    var $form = $('#modal_form');
    ev.preventDefault();
    $.ajax({
        xhr: function () {
            var progress = $('.progress'), xhr = $.ajaxSettings.xhr();

            progress.show();

            xhr.upload.onprogress = function (ev) {
                if (ev.lengthComputable) {
                    var percentComplete = parseInt((ev.loaded / ev.total) * 100);
                    progress.val(percentComplete);
                    if (percentComplete === 100) {
                        progress.hide().val(0);
                    }
                }
            };

            return xhr;
        },
        url: $form.attr('action'),
        type: 'POST',
        data: new FormData(this),
        contentType: false,
        cache: false,
        processData: false,
        beforeSend: function (XMLHttpRequest) {
            $('.progress').show;
            $("#submit").attr({disabled: "disabled"})
        },
        complete: function () {
            $("#submit").removeAttr("disabled");
        },
        success: function (data, status, xhr) {
            if (data['state'] == 'ok') {
                form_md.modal('close');
                $("#id_partner").append(
                    $('<option>', {value: data['partner_id'], text: data['partner_text'], selected: true})
                );
                $("#id_province").append(
                    $('<option>', {value: data['province_id'], text: data['province_text'], selected: true})
                );
                $("#id_city").append(
                    $('<option>', {value: data['city_id'], text: data['city_text'], selected: true})
                );
            }
            else {
                $('#form_modal .container').html(data);
                form_md.modal('open')
            }
        },
        error: function (xhr, status, error) {
            // ...
        }
    });
}));
// $('#submit').on('click', function (e) {
//     $('#modal_form').submit()
//
// });