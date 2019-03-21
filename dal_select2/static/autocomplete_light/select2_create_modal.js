;(function ($) {
    if (window.__dal__initListenerIsSet)
        return;
    $(document).on('autocompleteLightInitialize', '[data-autocomplete-light-function=select2_crate_modal]', function () {
        var element = $(this);

        // Templating helper
        function template(text, is_html) {
            if (is_html) {
                var $result = $('<span>');
                $result.html(text);
                return $result;
            } else {
                return text;
            }
        }

        function result_template(item) {
            return template(item.text,
                element.attr('data-html') !== undefined || element.attr('data-result-html') !== undefined
            );
        }

        function selected_template(item) {
            if (item.selected_text !== undefined) {
                return template(item.selected_text,
                    element.attr('data-html') !== undefined || element.attr('data-selected-html') !== undefined
                );
            } else {
                return result_template(item);
            }
            return
        }

        var ajax = null;
        if ($(this).attr('data-autocomplete-light-url')) {
            ajax = {
                url: $(this).attr('data-autocomplete-light-url'),
                dataType: 'json',
                delay: 250,

                data: function (params) {
                    var data = {
                        q: params.term, // search term
                        page: params.page,
                        create: element.attr('data-autocomplete-light-create') && !element.attr('data-tags'),
                        forward: yl.getForwards(element)
                    };

                    return data;
                },
                processResults: function (data, page) {
                    if (element.attr('data-tags')) {
                        $.each(data.results, function (index, value) {
                            value.id = value.text;
                        });
                    }

                    return data;
                },
                cache: true
            };
        }

        $(this).select2({
            tokenSeparators: element.attr('data-tags') ? [','] : null,
            debug: true,
            containerCssClass: ':all:',
            placeholder: element.attr('data-placeholder') || '',
            language: element.attr('data-autocomplete-light-language'),
            minimumInputLength: element.attr('data-minimum-input-length') || 0,
            allowClear: !$(this).is('[required]'),
            templateResult: result_template,
            templateSelection: selected_template,
            ajax: ajax,
            tags: Boolean(element.attr('data-tags')),
            createSearchChoice: function () {
                console.log(222)
            }
        });

        // window._select2.push(this);

        // $(this).on('select2:open', function (e) {
        //         alert('open');
        //         $(".select2-search__field").attr("readonly", true);
        //
        //         $(".select2-dropdown").bind("touchstart", function (e) {
        //                 $target = $(e.target);
        //                 if ($target.hasClass("select2-search__field")) {
        //                     $target.removeAttr("readonly").focus();
        //                 }
        //             }
        //         )
        //     }
        // );
        // $(this).on('select2:close', function (e) {
        //         alert('close');
        //
        //         $(".select2-dropdown").unbind("touchstart");
        //         $(".select2-search__field").removeAttr("readonly")
        //     }
        // );

        $(this).on('select2:selecting', function (e) {
            console.log(this);
            // alert('ok');

            var data = e.params.args.data;
            if (data.create_id !== true)

                return;

            e.preventDefault();
            var select = $(this);
            var ID = data.id;
            // console.log(data.id);
            // md_package_list.modal('open');
            var url = $(this).attr('data-create-url');
            $.ajax({
                url: url,
                method: 'GET',
                success: function (data) {
                    $('#form_modal .container').html(data);
                    $('#modal_form').attr('action', url);
                    // $('#modal_form').attr('')
                    $('#id_name').val(ID);
                    // when modal is open
                    form_md.modal('open');
                    select.select2('close');

                    // $('#modal1').removeAttr('tabindex');
                }
            });

        // $.ajax({
        //     url: $(this).attr('data-create-url'),
        //     type: 'GET',
        //     dataType: 'json',
        //     // data: {
        //     //     text: data.id,
        //     //     forward: yl.getForwards($(this))
        //     // },
        //     data: $(this).val(),
        //     beforeSend: function (xhr, settings) {
        //         xhr.setRequestHeader("X-CSRFToken", document.csrftoken);
        //     },
        //     success: function (data, textStatus, jqXHR) {
        //         $('#modal1 .container').html(data);
        //         md.modal('open');
        //         // select.append(
        //         //     $('<option>', {value: data.id, text: data.text, selected: true})
        //         // );
        //         // select.trigger('change');
        //         // select.select2('close');
        //     }
        // });
        return false;
        });



        // $(this).on('select2:selecting', function (e) {
        //
        //     var data = e.params.args.data;
        //
        //     if (data.create_id !== true)
        //         return;
        //
        //     e.preventDefault();
        //
        //     var select = $(this);
        //
        //     $.ajax({
        //         url: $(this).attr('data-autocomplete-light-url'),
        //         type: 'POST',
        //         dataType: 'json',
        //         data: {
        //             text: data.id,
        //             forward: yl.getForwards($(this))
        //         },
        //         beforeSend: function (xhr, settings) {
        //             xhr.setRequestHeader("X-CSRFToken", document.csrftoken);
        //         },
        //         success: function (data, textStatus, jqXHR) {
        //             select.append(
        //                 $('<option>', {value: data.id, text: data.text, selected: true})
        //             );
        //             select.trigger('change');
        //             select.select2('close');
        //         }
        //     });
        // });



    });
    window.__dal__initListenerIsSet = true;

    $('[data-autocomplete-light-function=select2]:not([id*="__prefix__"])').each(function () {
        window.__dal__initialize(this);


        // console.log(this)
    });


})(yl.jQuery);
