#ifndef FILE_SPACETIMEFE_HPP
#define FILE_SPACETIMEFE_HPP

// SpaceTimeFE based on:

/*********************************************************************/
/* File:   myElement.hpp                                             */
/* Author: Joachim Schoeberl                                         */
/* Date:   26. Apr. 2009                                             */
/*********************************************************************/


namespace ngfem
{


    class SpaceTimeFE : public ScalarFiniteElement<2>
   {
        ScalarFiniteElement<2>* sFE = nullptr;
        ScalarFiniteElement<1>* tFE = nullptr;
        double time;
        bool override_time = false;


    public:
      // constructor
      SpaceTimeFE (ScalarFiniteElement<2>* s_FE,ScalarFiniteElement<1>*t_FE, bool override_time, double time );

      virtual ELEMENT_TYPE ElementType() const { return ET_TRIG; }


      virtual void CalcShape (const IntegrationPoint & ip,
                              BareSliceVector<> shape) const;

      // for time derivatives

      virtual void CalcDtShape (const IntegrationPoint & ip,
                               BareSliceVector<> dshape) const;

      virtual void CalcDShape (const IntegrationPoint & ip,
                               SliceMatrix<> dshape) const;

      // there are some more functions to bring in ...
      //using ScalarFiniteElement<2>::CalcShape;
      //using ScalarFiniteElement<2>::CalcDShape;
    };


    class NodalTimeFE : public ScalarFiniteElement<1>
      {
        int vnums[2];
        int k_t;
      public:
        NodalTimeFE (int order);
        virtual ELEMENT_TYPE ElementType() const { return ET_SEGM; }
        void SetVertexNumber (int i, int v) { vnums[i] = v; }

        virtual void CalcShape (const IntegrationPoint & ip,
                                BareSliceVector<> shape) const;

        virtual void CalcDShape (const IntegrationPoint & ip,
                                 SliceMatrix<> dshape) const;

        void GetIntpPts (Vector<>& intp_pts) const;
        int order_time() const { return k_t; }

      private:
        template <class T>
        T Lagrange_Pol (T x, Vector<> intp_pts, int i) const;
      };

 }


#endif

