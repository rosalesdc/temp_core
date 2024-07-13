odoo.define('b_fast_invoicing.fast_invoicing', function (require) {
    "use strict";
    require('web.dom_ready');
    var Widget = require('web.Widget');

    const ajax = require('web.ajax');
    const core = require('web.core');
    const rpc = require('web.rpc');
    const Dialog = require('web.Dialog');
    const _t = core._t;
    var session = require('web.session');

    const publicWidget = require('web.public.widget');

    var framework = require('b_fast_invoicing.framework');

    publicWidget.registry.FastInvoicing = publicWidget.Widget.extend({
        selector: '.website_fast_invoicing',

        events: {
            'click a.make-invoice': '_onInvoiceClicked',
            'click a.edit-partner-info': '_onEditInfoClicked',
            'click a.edit-partner-info-pos': '_onEditInfoPosClicked',
            'click a.make-invoice-pos': '_onInvoicePosClicked',
            'change select[name=partner_country_id]': '_onChangeState',
            'click button.oe_search_button': '_onSearchClicked',
            'click button.vat1': '_onSearchClickedVat',
            'click a.confirm-button': '_onConfirmClicked',
            'keydown input.search-query': '_onKeyDownSearch',

        },

        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
        },
        /**
         * @override
         */
        start: function () {
            return this._super.apply(this, arguments);
        },
        /**
         *
         */
        _onConfirmClicked: function (e) {
            e.preventDefault();
            e.stopPropagation();
        },
        /**
         * TODO
         * @param title
         * @param message
         * @returns {*}
         */
        displayError: function (title, message) {
            return new Dialog(null, {
                title: _t('Error: ') + _.str.escapeHTML(title),
                size: 'medium',
                $content: "<p>" + (_.str.escapeHTML(message) || "") + "</p>",
                buttons: [
                    { text: _t('Ok'), close: true }]
            }).open();
        },
        /**
         *
         */
        _onChangeState: function () {
            console.log('_onChangeState');
            var partner_country_id = this.$el.find('select[name=partner_country_id]').val();
            var partner_state_id = this.$el.find('select[name=partner_state_id]');
            rpc.query({
                model: 'res.company',
                method: 'get_state_id',
                args: [[], partner_country_id],
            }).then(function (result) {
                console.log(result);
                partner_state_id.find('option').remove();
                for (const obj in result) {
                    partner_state_id.append($("<option />").val(result[obj][0]).text(result[obj][1])
                    );
                }
            })
        },
        /**
         *
         */
        _onInvoiceClicked: function () {
            var self = this;
            var access_token = this.$el.data('order');
            var form_values = {
                payment_method: this.$el.find('select[name=payment_method]').val(),
                cfdi_use: this.$el.find('select[name=cfdi_use]').val(),
                l10n_mx_edi_fiscal_regime: this.$el.find('select[name=l10n_mx_edi_fiscal_regime]').val(),
            };
            framework.blockUI()
            ajax.post('/autofactura/' + access_token + '/direct', form_values).then(function (res) {
                if (res) {
                    $(window.location).attr('href', res);
                } else {
                    self.displayError(_t('RFC'), _t('El número de RFC es requerido para realizar la autofactura.'))
                }
            }).then(function () {
                framework.unblockUI();
            });
        },
        /**
         *
         */
        _submit_values: function () {
            e.preventDefault();
            e.stopPropagation();

            var $form = modal.find('form');
            $form.find(".o_invalid_field").remove();
            var vat_container = $form.find('select[name=vat]');
            var name_container = $form.find('input[name=name]');
            var phone_container = $form.find('input[name=phone]');
            var email_container = $form.find('input[name=email]');
            var l10n_mx_edi_fiscal_regime_container = $form.find('select[name=l10n_mx_edi_fiscal_regime]');
            if (vat_container.length === 0) {
                vat_container = $form.find('input[name=vat]');
            }
            var vat = vat_container.val();
            var name = name_container.val();
            var phone = phone_container.val();
            var email = email_container.val();
            var l10n_mx_edi_fiscal_regime = l10n_mx_edi_fiscal_regime_container.val();

            var flag_error = false;
            if (!l10n_mx_edi_fiscal_regime) {
                $form.find('div.l10n_mx_edi_fiscal_regime').append('<div style="color: red;" class="o_invalid_field" aria-invalid="true">El RFC es requerido</div>');
                flag_error = true;
            }
            if (!vat) {
                $form.find('div.vat').append('<div style="color: red;" class="o_invalid_field" aria-invalid="true">El RFC es requerido</div>');
                flag_error = true;
            }
            if (!name) {
                $form.find('div.name').append('<div style="color: red;" class="o_invalid_field" aria-invalid="true">El nombre es requerido</div>');
                flag_error = true;
            }
            if (!phone) {
                $form.find('div.phone').append('<div style="color: red;" class="o_invalid_field" aria-invalid="true">El telefono es requerido</div>');
                flag_error = true;
            }
            if (!email) {
                $form.find('div.email').append('<div style="color: red;" class="o_invalid_field" aria-invalid="true">El correo es requerido</div>');
                flag_error = true;
            }
            if (!flag_error) {
                rpc.query({
                    route: '/autofactura/vat/validation',
                    params: {
                        vat: $form.find('select[name=vat]').val() || $form.find('input[name=vat]').val(),
                        country_id: $form.find('input[name=country_id]').val()
                    }
                }).then(function (res) {
                    if (res.error) {
                        $form.find('div.vat').append('<div style="color: red;" class="o_invalid_field" aria-invalid="true">' + res.error + '</div>');
                    } else {
                        vat_container.val(res.vat);
                        $form.submit();

                    }
                })
            }
        },
        /*_search_data : function(){

        },*/

        _onEditInfoClicked: function () {
            var access_token = this.$el.data('order');
            var vat_el = this.$el.find('input[name=vat_cont]').val()

            var form_values = {
                payment_method: this.$el.find('select[name=payment_method]').val(),
                cfdi_use: this.$el.find('select[name=cfdi_use]').val(),
                vat: this.$el.find('input[name=vat_cont]').val(),
                l10n_mx_edi_fiscal_regime: this.$el.find('select[name=l10n_mx_edi_fiscal_regime]').val(),
            };
            framework.blockUI();

            return $.get('/autofactura/invoicing/' + vat_el + '/' + access_token, form_values).done(function (response) {
                var modal = $(response);
                var self = this;
                modal.modal('show');
                modal.on('click', '.search', function (e) {
                    var $form = modal.find('form');
                    e.preventDefault();
                    e.stopPropagation();
                    $form.find(".o_invalid_field").remove();

                    var vat_container = $form.find('input[name=vat]');
                    var name_container = $form.find('input[name=name]');
                    var phone_container = $form.find('input[name=phone]');
                    var email_container = $form.find('input[name=email]');
                    var l10n_mx_edi_fiscal_regime_container = $form.find('select[name=l10n_mx_edi_fiscal_regime]');

                    var vat = vat_container.val();
                    if (!vat) {
                        $form.find('div.vat').append('<div style="color: red;" class="o_invalid_field" aria-invalid="true">El RFC es requerido</div>');

                    }
                    rpc.query({
                        route: '/autofactura/autocomplete',
                        params: {
                            vat: $form.find('input[name=vat]').val()
                        }
                    }).then(function (data) {
                        // Aqui hacemos el autocompletamiento
                        name_container.val(data.name);
                        phone_container.val(data.phone);
                        email_container.val(data.email);
                        l10n_mx_edi_fiscal_regime_container.val(data.l10n_mx_edi_fiscal_regime);

                        if (vat) {
                            if (data.partner == true) {
                                name_container.prop("disabled", true);
                                if (data.phone != '') {
                                    phone_container.prop("disabled", true);
                                }
                                else {
                                    phone_container.prop("disabled", false);
                                }
                                if (data.email != '') {
                                    email_container.prop("disabled", true);
                                }
                                else {
                                    email_container.prop("disabled", false);
                                }
                                if (data.l10n_mx_edi_fiscal_regime != '') {
                                    l10n_mx_edi_fiscal_regime_container.prop("disabled", true);
                                }
                                else {
                                    l10n_mx_edi_fiscal_regime_container.prop("disabled", false);
                                }
                            } else {
                                name_container.prop("disabled", false);
                                phone_container.prop("disabled", false);
                                email_container.prop("disabled", false);
                                l10n_mx_edi_fiscal_regime_container.prop("disabled", false);
                            }
                            $('#name-grouper').css('display', '');
                            $('#phone-grouper').css('display', '');
                            $('#email-grouper').css('display', '');
                            $('#l10n-mx-edi-fiscal-regime-grouper').css('display', '');
                        }
                        $('button.submit').prop('disabled', false);
                    })
                });
                modal.on('click', 'button.submit', function (e) {
                    self._submit_values;
                });

            }).then(function () {
                framework.unblockUI();
            });
        },
        /**
         *
         */
        _onEditInfoPosClicked: function () {
            var access_token = this.$el.data('order');
            var vat_el = this.$el.find('input[name=vat_cont]').val()
            var form_values = {
                cfdi_use: this.$el.find('select[name=cfdi_use]').val(),
                vat: this.$el.find('input[name=vat_cont]').val(),
                tpv: 1,
                l10n_mx_edi_fiscal_regime: this.$el.find('select[name=l10n_mx_edi_fiscal_regime]').val(),
            };
            framework.blockUI();
            return $.get('/autofactura/invoicing/pos/' + vat_el + '/' + access_token, form_values).done(function (response) {
                var modal = $(response);
                modal.modal('show');
                modal.on('click', '.search', function (e) {
                    var $form = modal.find('form');
                    e.preventDefault();
                    e.stopPropagation();
                    $form.find(".o_invalid_field").remove();
                    $('button.submit').prop('disabled', true);

                    var vat_container = $form.find('input[name=vat]');
                    var name_container = $form.find('input[name=name]');
                    var phone_container = $form.find('input[name=phone]');
                    var email_container = $form.find('input[name=email]');
                    var l10n_mx_edi_fiscal_regime_container = $form.find('select[name=l10n_mx_edi_fiscal_regime]');


                    var vat = vat_container.val();

                    if (!vat) {
                        $form.find('#vat-grouper').after('<div style="color: red; text-align:center;" class="o_invalid_field" aria-invalid="true">El RFC es requerido.</div>');
                        $('#name-grouper').css('display', 'none');
                        $('#phone-grouper').css('display', 'none');
                        $('#email-grouper').css('display', 'none');
                        $('#l10n-mx-edi-fiscal-regime-grouper').css('display', 'none');
                        return;
                    }
                    if (vat) {
                        rpc.query({
                            model: 'res.partner',
                            method: 'check_vat_mx',
                            args: [[], vat],
                        }).then(function (result) {
                            if (result === true) {
                                rpc.query({
                                    route: '/autofactura/autocomplete',
                                    params: {
                                        vat: $form.find('input[name=vat]').val()
                                    }
                                }).then(function (data) {
                                    // Aqui hacemos el autocompletamiento
                                    name_container.val(data.name);
                                    phone_container.val(data.phone);
                                    email_container.val(data.email);
                                    l10n_mx_edi_fiscal_regime_container.val(data.l10n_mx_edi_fiscal_regime)
                                    $('button.submit').prop('disabled', false);

                                    if (vat) {
                                        if (data.partner == true) {
                                            name_container.prop("disabled", true);
                                            if (data.phone != '') {
                                                phone_container.prop("disabled", true);
                                            }
                                            else {
                                                phone_container.prop("disabled", false);
                                            }
                                            if (data.email != '') {
                                                email_container.prop("disabled", true);
                                            }
                                            else {
                                                email_container.prop("disabled", false);
                                            }
                                            if (data.l10n_mx_edi_fiscal_regime != '') {
                                                l10n_mx_edi_fiscal_regime_container.prop("disabled", true);
                                            }
                                            else {
                                                l10n_mx_edi_fiscal_regime_container.prop("disabled", false);
                                            }

                                        } else {
                                            name_container.prop("disabled", false);
                                            phone_container.prop("disabled", false);
                                            email_container.prop("disabled", false);
                                            email_container.prop("disabled", false);
                                            l10n_mx_edi_fiscal_regime_container.prop("disabled", false);
                                        }
                                    }
                                    $('#name-grouper').css('display', '');
                                    $('#phone-grouper').css('display', '');
                                    $('#email-grouper').css('display', '');
                                    $('#l10n-mx-edi-fiscal-regime-grouper').css('display', '');
                                })
                            }
                            if (result === false) {
                                $form.find('#vat-grouper').after('<div style="color: red; text-align:center;" class="o_invalid_field" aria-invalid="true">El RFC introducido es incorrecto.</div>');
                                $('#name-grouper').css('display', 'none');
                                $('#phone-grouper').css('display', 'none');
                                $('#email-grouper').css('display', 'none');
                                $('#l10n-mx-edi-fiscal-regime-grouper').css('display', 'none');
                                return;
                            }
                        })
                    }
                });
                modal.on('click', 'button.submit', function (e) {
                    self._submit_values;

                });

                modal.find('button.search').trigger("click");

            }).then(function () {
                framework.unblockUI();
            });
        },
        /**
         *
         */
        _onInvoicePosClicked: function () {
            var self = this;
            var access_token = this.$el.data('order');
            var form_values = {
                cfdi_use: this.$el.find('select[name=cfdi_use]').val(),
                tpv: 1,
                l10n_mx_edi_fiscal_regime: this.$el.find('select[name=l10n_mx_edi_fiscal_regime]').val(),
            };
            framework.blockUI();
            ajax.post('/autofactura/' + access_token + '/direct', form_values).then(function (res) {
                if (res) {
                    $(window.location).attr('href', res);
                } else {
                    self.displayError(_t('RFC'), _t('El número de RFC es requerido para realizar la auto factura.'))
                }
            }).then(function () {
                framework.unblockUI();
            });
        },
        /**
         *
         */

        _onSearchClicked: function () {
            var self = this;
            var search_query = this.$el.find('input.search-query').val();
            var vat = this.$el.find('input[name=vat_cont]').val();
            if (search_query) {
                return ajax.jsonRpc('/autofactura/search', 'call', {
                    search: search_query
                }).then(function (res) {
                    var access_token = res.access_token;
                    var is_allowed = res.is_allowed;
                    if (is_allowed) {
                        if (access_token) {

                            if (res.is_pos) {
                                window.location.href = '/autofactura/pedido/tpv/' + vat + '/' + access_token;
                            } else {
                                window.location.href = '/autofactura/pedido/' + vat + '/' + access_token;
                            }
                        }
                        else {

                            var is_not_sale = res.is_not_sale;
                            if (is_not_sale) {
                                $.get('/autofactura/search/not_confirmed?search_query=' + search_query).done(function (response) {
                                    self.$el.append($(response));
                                });
                            }
                            else {
                                $.get('/autofactura/search/not_found?search_query=' + search_query).done(function (response) {
                                    self.$el.append($(response));
                                });

                            }
                        }
                    }
                    else{
                        $.get('/autofactura/search/not_allowed?search_query=' + search_query).done(function (response) {
                            self.$el.append($(response));
                        });
                    }

                });
            } else {
                $.get('/autofactura/search/not_allowed?search_query=' + search_query).done(function (response) {
                    self.$el.append($(response));
                });
            }
        },
        /**
         *
         */

        _onSearchClickedVat: function () {

            var $form = this.$el.find('select[name=vat1]').val() || this.$el.find('input[name=vat1]').val();
            var $message = this.$el.find('div.vat1');
            var $cont_btn = this.$el.find('div[name=cont_btn]');
            var $partner_regis = this.$el.find('div[name=div-partner-register]');
            var $test_vat = this.$el.find('input[name=test_vat]');
            $message.find('span.message').remove();
            rpc.query({
                route: '/autofactura/vat/validation',
                params: {
                    vat: $form,
                    country_id: false
                }
            }).then(function (res) {
                if (res.error) {
                    $cont_btn.css({ 'visibility': 'hidden' });
                    $cont_btn.find('a.btn-primary').remove();
                    $test_vat.val($form);
                    $message.append("<span class='message'>" + res.error + "</span>");
                    $partner_regis.css({ 'visibility': 'hidden' });
                } else {
                    rpc.query({
                        route: '/autofactura/autocomplete',
                        params: {
                            vat: $form
                        }
                    }).then(function (data) {
                        $cont_btn.css({ 'visibility': 'hidden' });
                        $cont_btn.find('a.btn-primary').remove();
                        $message.find('span.message').remove();
                        if (data.partner) {
                            $message.append('<span class="message">Este Cliente esta registrado con el nombre ' + data.name + '</span>');
                            $cont_btn.css({ 'visibility': 'initial' });
                            $partner_regis.css({ 'visibility': 'hidden' });
                            $cont_btn.append('<a class="btn btn-primary" name="cont_btn" style="display: block;" href="/autofactura/' + data.vat + '">Continue</a>');
                        }
                        else {
                            $test_vat.val($form);
                            $message.append('<span class="message">Este Cliente no se encuentra registrado</span>');
                            $cont_btn.css({ 'visibility': 'hidden' });
                            $partner_regis.css({ 'visibility': 'initial' });

                        }
                    })

                }
            })

        },
        /**
         *
         *
         * @private
         * @param event
         */
        _onKeyDownSearch: function (event) {
            var self = this;
            switch (event.keyCode) {
                case $.ui.keyCode.ENTER:
                    event.preventDefault();
                    self._onSearchClicked();
                    break;
            }
        },
    });

    publicWidget.registry.FastInvoicingError = publicWidget.Widget.extend({
        selector: '.website_fast_invoicing_error',

        events: {
            'click .o_fi_clipboard_button': '_onMessagePostClick',
        },

        /**
         * @constructor
         */
        init: function () {
            this._super.apply(this, arguments);
            this.sendCounter = 0;
        },

        _onMessagePostClick: function (ev) {
            var self = this;
            var $btn = $(ev.currentTarget);
            if (this.sendCounter > 0) {
                return;
            }
            $btn.tooltip({
                title: _t('Enviado !'),
                trigger: "manual",
                placement: "bottom"
            });
            var orderId = $btn.data('id');
            ajax.jsonRpc('/autofactura/message/post', 'call', {
                order_id: orderId,
                message: this.$('#o_error_message').html()
            }).then(function (data) {
                if (data) {
                    self.sendCounter += 1;
                    $btn.attr('disabled', true);
                    _.defer(function () {
                        $btn.tooltip("show");
                        _.delay(function () {
                            $btn.tooltip("hide");
                        }, 800);
                    });
                }
            }).guardedCatch(function () {
                alert("Error");
            });
        }
    });

});