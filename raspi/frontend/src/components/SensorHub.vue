
<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Sensor Hub</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="sendCommand">
              <v-text-field
                label="Command"
                v-model="command"
              />
              <v-btn type="submit" color="primary">Send Command</v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Sensor Data</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="(data, index) in sensorData"
                :key="index"
              >
                <v-list-item-content>
                  <v-list-item-title>{{ data }}</v-list-item-title>
                </v-list-item-content>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import axios from 'axios';

export default {
  name: 'SensorHub',
  data() {
    return {
      command: 'GET_DATA',
      sensorData: [],
    };
  },
  mounted() {
    axios.get('/sensor-hub/read')
      .then(response => {
        this.sensorData = response.data.data;
      });
  },
  methods: {
    sendCommand() {
      axios.post('/sensor-hub/send-command', { command: this.command })
        .then(response => {
          this.$emit('notify', response.data.message);
        });
    },
  },
};
</script>
