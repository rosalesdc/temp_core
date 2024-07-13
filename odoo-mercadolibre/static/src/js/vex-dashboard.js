/** @odoo-module **/

import { loadBundle, loadJS } from "@web/core/assets";
import { Component, onWillUnmount, useEffect, useRef, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
//import Chart from "chart.js/auto";

class Welcome extends Component {
    static template = "odoo-mercadolibre.welcome";

    setup() {
        this.http = useService("http");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");
        this.state = useState({
            title: "",
            description: "",
            segments: [],
            selectedSegment: null,
            column: "",
            items: [
                // { w: 2, h: 2, content: 'my first widget' }, 
                // { w: 2, content: 'another longer widget!' } 
            ]
        });
        
        this.canvasRef = useRef("productosSincronizadosChart");
        this.canvasRef2 = useRef("categoriasProductosChart");
        this.canvasRef3 = useRef("pie1");
        this.canvasRef4 = useRef("line1");
        this.canvasRef5 = useRef("bar1");
        this.canvasRef6 = useRef("radar1");
        this.canvasRef7 = useRef("doughnut1");
        this.canvasRef8 = useRef("polarArea1");
        this.canvasRef9 = useRef("bubble1");
        this.chart = null;
        this.chart2 = null;
        this.chart3 = null;
        this.chart4 = null;
        this.chart5 = null;
        this.chart6 = null;
        this.chart7 = null;
        this.chart8 = null;
        this.chart9 = null;

        this.fetchPartnersAsSegments();

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js")
        });

        // Inicializar los "segmentos" (partners) al montar el componente
        onWillStart(async () => {
            await this.fetchPartnersAsSegments();
            this.addBackground()
        });

        useEffect(() => {
            const grid = GridStack.init({
                cellHeight: 'auto',
                animate: false, // show immediate (animate: true is nice for user dragging though)
                // columnOpts: {
                //     columnWidth: 100, // wanted width
                // },
            }).on('change', (ev, gsItems) => {
                this.column = grid.getColumn();
                console.log(this.column)
            });;

            this.renderChart();
            this.renderChart2();
            this.renderChart3();
            this.renderChart4();
            this.renderChart5();
            this.renderChart6();
            this.renderChart7();
            this.renderChart8();
            this.renderChart9();


            grid.load(this.state.items);

        });
        onWillUnmount(() => {
            this.onWillUnmount()
            this.delBackground()
        });
    }



    addBackground() {
        const actionManagerEl = document.querySelector('.o_action_manager');
        if (actionManagerEl) {
            actionManagerEl.id = 'doodles';
            actionManagerEl.classList.add('list-contact');
        } else {
            console.warn('Elemento .o_action_manager no encontrado.');
        }
    }

    delBackground() {
        const actionManagerEl = document.querySelector('.o_action_manager');
        if (actionManagerEl.id = 'doodles') {
            actionManagerEl.id = null;
            actionManagerEl.classList.remove('list-contact');
        } else {
            console.warn('Elemento .o_action_manager no encontrado.');
        }
    }

    // NO FUNCIONA HTTP :(
    async fetchPartnersAsSegments() {
        try {
            const response = await this.http.request({
                url: "/api/partners/details",
                method: "POST",
                params: {}, // Cualquier parámetro adicional necesario
            });

            if (response.success) {
                console.log(response)
                this.state.segments = response.partners.map(partner => ({
                    id: partner.id,
                    name: partner.name,
                }));
                this.notificationService.add(_t("Se cargo los clientes con éxito."), {
                    type: "success", // Esto mostrará la notificación como un mensaje de éxito
                    title: _t("Mensaje Enviado"),
                });
            } else {
                // Manejo en caso de respuesta no exitosa
                this.notificationService.add("No se pudieron cargar los datos", { type: 'danger' });
            }
        } catch (error) {
            // Manejo en caso de error en la petición
            console.error("Error al obtener los detalles de los partners:", error);
            this.notificationService.add("Error al cargar los datos", { type: 'danger' });
        }
    }

    async openModal() {
        // this.dialog.add(FormViewDialog, {
        //     resModel: "message.mass_send", // Asumiendo que este es tu modelo para enviar mensajes masivos
        //     context: {
        //         // Pasar los valores actuales del estado como contexto predeterminado para el formulario
        //         default_title: this.state.title,
        //         default_description: this.state.description,
        //         default_segment_id: this.state.selectedSegment?.id,
        //         // Asumiendo que el campo 'segments' se maneja de alguna manera en tu modelo, podrías necesitar adaptar esta parte
        //     },
        //     title: _t("Enviar Mensaje Masivo"), // Título del diálogo del formulario
        //     onRecordSaved: this.onMassMessageSent.bind(this), // Opcional: Un callback que se llama después de guardar el registro correctamente
        // });
    }

    onMassMessageSent() {
        // Verifica si se ha seleccionado un segmento
        if (!this.state.selectedSegment) {
            this.notificationService.add(_t("Por favor, seleccione un segmento primero."), {
                type: "danger",
            });
            return;
        }

        this.notificationService.add(_t("Abriría un modal para enviar mensajes a: ") + this.state.selectedSegment.name, {
            type: "info",
        });
        // Aquí puedes definir lo que sucede después de enviar el mensaje masivo
        // Por ejemplo, mostrar una notificación de éxito o actualizar algún componente en la UI
        this.notificationService.add(_t("El mensaje masivo ha sido enviado con éxito."), {
            type: "success", // Esto mostrará la notificación como un mensaje de éxito
            title: _t("Mensaje Enviado"),
        });
        // Otras acciones después de enviar el mensaje
    }

    // Adaptación para buscar 'partners' y considerarlos como 'segmentos'
    async fetchPartnersAsSegments() {
        // Nota: Aquí estamos usando 'name' e 'id', pero puedes ajustarlo según sea necesario
        const fields_to_fetch = [
            "id", "company_id", "create_date", "name", "title", "parent_id",
            "user_id", "state_id", "country_id", "industry_id", "color",
            "commercial_partner_id", "create_uid", "write_uid",
            "ref", "lang", "tz", "vat", "company_registry", "website", "function",
            "type", "street", "street2", "zip", "city", "email", "phone", "mobile",
            "commercial_company_name", "company_name", "date", "comment",
            "partner_latitude", "partner_longitude", "active", "employee",
            "is_company", "partner_share", "write_date", "message_bounce",
            "email_normalized", "signup_type", "signup_expiration", "signup_token",
            "team_id", "partner_gid", "additional_info",
            "phone_sanitized"
        ]
        const partners = await this.orm.call("res.partner", "search_read", [[]], { fields: fields_to_fetch });
        console.log(partners);
        this.state.segments = partners.map(partner => ({
            // Asigna cada 'partner' a un formato de 'segmento', si necesario
            id: partner.id,
            name: partner.name
        }));
    }

    selectSegment(ev) {
        this.state.selectedSegment = this.state.segments.find(segment => segment.id == ev.target.value);
        console.log(this.state);
    }

    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(this.canvasRef.el, {
            type: "line",
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio'],
                datasets: [{
                    label: 'Historico de ventas Mes a Mes',
                    data: [50, 60, 70, 80,56, 100],
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Historico de ventas Mes a Mes', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }



    renderChart2() {
        if (this.chart2) {
            this.chart2.destroy();
        }

        this.chart2 = new Chart(this.canvasRef2.el, {
            type: "line",
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril'],
                datasets: [
                    {
                    label: 'Organicas',
                    data: [50, 60, 70, 80],
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },
                {
                    label: 'Pagadas',
                    data: [50, 53, 40, 60],
                    backgroundColor: 'rgba(144, 238, 144, 0.5)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }                
            
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Historico de ventas Mes a Mes', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderChart3() {
        if (this.chart3) {
            this.chart3.destroy();
        }

        this.chart3 = new Chart(this.canvasRef3.el, {
            type: "line",
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril'],
                datasets: [
                    {
                    label: 'Clientes Nuevos',
                    data: [20, 40, 60, 80]                    ,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },
                {
                    label: 'Recurrentes',
                    data: [10, 30, 50, 70]                    ,
                    backgroundColor: 'rgba(144, 238, 144, 0.5)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }                
            
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Índice de Recompra', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderChart4() {
        if (this.chart4) {
            this.chart4.destroy();
        }

        this.chart4 = new Chart(this.canvasRef4.el, {
            type: "line",
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril'],
                datasets: [
                    {
                    label: 'Clientes Nuevos',
                    data: [35, 35, 75, 20]                    ,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },              
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Frecuencia de Re compra', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderChart5() {
        if (this.chart5) {
            this.chart5.destroy();
        }

        this.chart5 = new Chart(this.canvasRef5.el, {            
        type: "line",
        data: {
            labels: ['Enero', 'Febrero', 'Marzo', 'Abril'],
            datasets: [
                {
                label: 'Organicas',
                data: [50, 60, 70, 80],
                backgroundColor: 'rgba(75, 92, 292, 0.4)',
                borderColor: 'rgba(75, 92, 292, 0.4)',
                tension: 0.1
            },
            {
                label: 'Pagadas',
                data: [50, 53, 40, 60],
                backgroundColor: 'rgba(120, 38, 144, 0.5)',
                borderColor: 'rgba(120, 38, 144, 0.5)',
                tension: 0.1
            }                
        
        ]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Visitas Organicas vs Pagadas', // Título principal
                    font: {
                        size: 24 // Tamaño del texto del título
                    }
                },
            },
            maintainAspectRatio: false,
            scales: {
                y: {
                    stacked: true,
                    grid: {
                        display: true,
                        color: "rgba(255,99,132,0.2)"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
    }

    renderChart6() {
        if (this.chart6) {
            this.chart6.destroy();
        }

        this.chart6 = new Chart(this.canvasRef6.el, {
            type: "bar",
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril', ' Mayo', 'Junio'],
                datasets: [
                    {
                    label: 'Historico',
                    data: [15, 35, 55, 75, 52, 33]                    ,
                    backgroundColor: 'rgba(248, 186, 215, 0.6)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },             
            
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Ánalisis de Resultados de Campaña por mes', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderChart7() {
        if (this.chart7) {
            this.chart7.destroy();
        }

        this.chart7 = new Chart(this.canvasRef7.el, {
            type: "bar",
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril'],
                datasets: [
                    {
                    label: 'Venta Total - Comisiones, envios y Ads',
                    data: [20, 40, 60, 80]                    ,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },             
            
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Márgenes totales de Tienda', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderChart8() {
        if (this.chart8) {
            this.chart8.destroy();
        }

        this.chart8 = new Chart(this.canvasRef8.el, {
            type: "bar",
            data: {
                labels: ['Decoraciones', 'Exteriores', 'Jardines', 'Botánica', 'Deportes', 'Remate'],
                datasets: [
                    {
                    label: 'Historico',
                    data: [15, 35, 55, 75, 52, 73]                    ,
                    backgroundColor: 'rgba(248, 186, 215, 0.6)',
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                },             
            
            ]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Tendencias de Keyboards en Mercadolibre de Categorías', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        stacked: true,
                        grid: {
                            display: true,
                            color: "rgba(255,99,132,0.2)"
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

    renderChart9() {
        if (this.chart9) {
            this.chart9.destroy();
        }

        this.chart9 = new Chart(this.canvasRef9.el, {
            type: "line",
            data: {
                labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', ],
                datasets: [{
                    label: 'Historico de ventas Mes a Mes',
                    data: [5000, 6000, 7000, 8000,5600, 5000],
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Margen de venta 2024 (ARS)', // Título principal
                        font: {
                            size: 24 // Tamaño del texto del título
                        }
                    },
                },
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    onWillUnmount() {
        if (this.chart) {
            this.chart.destroy();
        }
        if (this.chart2) {
            this.chart2.destroy();
        }
    }

    async sendMassMessage() {
        if (!this.state.selectedSegment) {
            alert("Por favor, seleccione un segmento antes de enviar.");
            return;
        }

        const success = await this.orm.call(
            "res.partner.segment",
            "send_mass_message",
            // AQUÍ CAMBIAS AL MODELO DE SEGMENTOS DE ODOO ESTO ES SOLO PRUEBA
            [this.state.selectedSegment, this.state.title, this.state.description]
        );

        if (success) {
            alert("Mensaje enviado exitosamente.");
        } else {
            alert("Hubo un error al enviar el mensaje.");
        }

        this.toggleModal(false);
    }
}

registry.category("actions").add("odoo-mercadolibre.welcome", Welcome);


