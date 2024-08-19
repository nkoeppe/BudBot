
<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>Water & Nutrient Management</v-card-title>
          <v-card-text>
            <v-form @submit.prevent="fillWater">
              <v-text-field
                label="Amount of Water (ml)"
                v-model="ml"
                type="number"
              />
              <v-btn type="submit" color="primary">Fill Water</v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import axios from 'axios';

export default {
  name: 'WaterNutrient',
  data() {
    return {
      ml: 5000,
    };
  },
  methods: {
    fillWater() {
      axios.post('/water-nutrient/fill-water', { ml: this.ml })
        .then(response => {
          this.$emit('notify', response.data.message);
        });
    },
  },
};
</script>
