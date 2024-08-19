
import Vue from 'vue';
import VueRouter from 'vue-router';
import Dashboard from './components/Dashboard.vue';
import Status from './components/Status.vue';
import WaterNutrient from './components/WaterNutrient.vue';
import EventManagement from './components/EventManagement.vue';
import SensorHub from './components/SensorHub.vue';
import Configuration from './components/Configuration.vue';

Vue.use(VueRouter);

const routes = [
  { path: '/', component: Dashboard },
  { path: '/status', component: Status },
  { path: '/water-nutrient', component: WaterNutrient },
  { path: '/events', component: EventManagement },
  { path: '/sensor-hub', component: SensorHub },
  { path: '/config', component: Configuration }
];

const router = new VueRouter({
  routes
});

export default router;
