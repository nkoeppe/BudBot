
<template>
  <v-app-bar app color="primary" dark>
    <v-toolbar-title>Control System Dashboard</v-toolbar-title>
    <v-spacer></v-spacer>
    <v-btn text to="/">Dashboard</v-btn>
    <v-btn text to="/status">Status</v-btn>
    <v-btn text to="/water-nutrient">Water & Nutrient</v-btn>
    <v-btn text to="/events">Events</v-btn>
    <v-btn text to="/sensor-hub">Sensor Hub</v-btn>
    <v-btn text to="/config">Configuration</v-btn>
  </v-app-bar>
</template>

<script>
export default {
  name: 'Navigation',
};
</script>
