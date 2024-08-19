
<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Control Status</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                v-for="status in statuses"
                :key="status.pin"
              >
                <v-list-item-content>
                  <v-list-item-title>Pin: {{ status.pin }}</v-list-item-title>
                  <v-list-item-subtitle>Status: {{ status.state }}</v-list-item-subtitle>
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
  name: 'Status',
  data() {
    return {
      statuses: [],
    };
  },
  mounted() {
    axios.get('/control/status')
      .then(response => {
        this.statuses = response.data.status;
      });
  },
};
</script>
